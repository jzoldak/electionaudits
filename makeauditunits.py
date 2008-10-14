#!/usr/bin/env python
"""Produce a report of audit units from incremental cumulative reports
made with Hart's Tally software.

%InsertOptionParserUsage%
"""

import os
import sys
import optparse
import logging
import csv
from datetime import datetime

from django.core.management import setup_environ
from django.db import transaction
import electionaudit.models as models
import electionaudit.util as util

__author__ = "Neal McBurnett <http://neal.mcburnett.org/>"
__copyright__ = "Copyright (c) 2008 Neal McBurnett"
__license__ = "MIT"


usage = """Usage: makeauditunits.py [options] [file]....

Example:
 makeauditunits.py -s 001_EV_p001.xml 002_AB_p022.xml 003_EL_p015.xml"""

parser = optparse.OptionParser(prog="makeauditunits", usage=usage)

parser.add_option("-s", "--subtract",
                  action="store_true", default=False,
                  help="Input files are incremental snapshots.   Subtract data in each file from previous data to generate batch results" )

parser.add_option("-m", "--min_ballots", dest="min_ballots", type="int",
                  default=5,
                  help="combine audit units with less than MINIMUM contest ballots", metavar="MINIMUM")

parser.add_option("-c", "--contest", dest="contest",
                  help="report on CONTEST", metavar="CONTEST")

parser.add_option("-v", "--verbose",
                  action="store_true", default=False,
                  help="Verbose output" )

parser.add_option("-d", "--debug",
                  action="store_true", default=False,
                  help="turn on debugging output")

# incorporate OptionParser usage documentation into our docstring
__doc__ = __doc__.replace("%InsertOptionParserUsage%\n", parser.format_help())

def main(parser):
    "Produce a report of audit units, subtracting each file from previous"

    (options, args) = parser.parse_args()

    if options.debug:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    logging.basicConfig(level=loglevel) # format='%(message)s'

    logging.debug("args = %s" % args)

    if len(args) == 0:
        args.append(os.path.join(os.path.dirname(__file__), 'testdata/testcum.xml'))
        logging.debug("using test file: " + args[0])

    totals = {}

    from audittools import settings
    setup_environ(settings)

    for file in args:
        if file.endswith(".xml"):
            newtotals = parse_xml_crystal(file, options)
            make_audit_unit(totals, newtotals, options)
            totals = newtotals
        elif file.endswith(".csv"):
            parse_csv(file, options)

    # Update tallies on all contests, just in case
    for contest in models.Contest.objects.all():
        contest.tally()

@transaction.commit_on_success
def parse_csv(file, options):
    """Parse a csv file of election data.  The model of this format
    is the San Mateo precinct spreadsheet in "testdata/test.csv".
    If the data is to be aggregated for privacy (the default), the data
    should be sorted by batch (precinct).
    """

    election = os.path.basename(file)[0:-4]

    reader = csv.DictReader(open(file))

    au_AB = util.AuditUnit()
    au_EL = util.AuditUnit()

    for r in reader:
        batch = [r['Precinct_name']]
        contest = r['Contest_title']
        if r['Party_Code']:
            contest += ":" + r['Party_Code']
        choice = r['candidate_name']

        if batch != au_AB.batches  or  contest != au_AB.contest:
            logging.debug("new batch '%s' at line %d" % (batch, reader.reader.line_num))
            util.pushAuditUnit(au_AB, min_ballots = options.min_ballots)
            au_AB = util.AuditUnit(election, contest, 'AB', batch)
            util.pushAuditUnit(au_EL, min_ballots = options.min_ballots)
            au_EL = util.AuditUnit(election, contest, 'EL', batch)
        
        au_AB.update(choice, r['absentee_votes'])
        au_EL.update(choice, r['election_votes'])
        if r['cand_seq_nbr'] == '1':	# duplicated for each candidate - silly
            au_AB.update('Under', r['absentee_under_votes'])
            au_AB.update('Over', r['absentee_over_votes'])
            au_EL.update('Under', r['election_under_votes'])
            au_EL.update('Over', r['election_over_votes'])

    util.flushPipes()

@transaction.commit_on_success
def parse_xml_crystal(file, options):
    """Extract relevant data from each contest in a given crystalreports xml
    file"""

    import lxml.etree as ET

    election, created = models.CountyElection.objects.get_or_create(name="BoulderGeneral")
    if os.path.basename(file) == "cumulative.xml":
        # if it's the borind default, use alternate naming scheme:
        #  parent directory of canonical path
        name = os.path.basename(os.path.dirname(os.path.realpath(file)))
    else:
        name = os.path.basename(file)[0:-4] 	# trim directory and ".xml"

    absentee_batch, created = models.Batch.objects.get_or_create(
        name=name,
        election=election,
        type="AB" )
    early_batch, created = models.Batch.objects.get_or_create(
        name=name,
        election=election,
        type="EV" )
    election_batch, created = models.Batch.objects.get_or_create(
        name=name,
        election=election,
        type="EL" )

    # filter out this confounding unprefixed namespace attribute
    # ...or figure out how to parse it...
    filterout = "xmlns = 'urn:crystal-reports:schemas'"
    import StringIO
    newfile = StringIO.StringIO()
    newfile.write(open(file).read().replace(filterout, ""))
    newfile.seek(0)

    root = ET.parse(newfile).getroot()
    logging.debug("root = %s" % root)

    # The Hart system forces the use of some odd contest names.
    # This is a table of fixes for them.
    replacements = [
        (", Vote For 1", ""),
        ("THE EARNINGS FROM THE INVESTMENT", "ST VRAIN VALLEY SCHOOL DISTRICT NO. RE-1J  BALLOT ISSUE NO. 3B"),
        ]

    values = {}

    for contesttree in root.xpath('//FormattedAreaPair[@Type="Group"]'):
        tree = contesttree.xpath('FormattedArea[@Type="Header"]//FormattedReportObject[@FieldName="{@district_info}"]/FormattedValue')
        if len(tree) != 1:
            logging.error("Error: number of Headers should be 1, not %d.  Line %d" % (len(tree), contesttree.sourceline))
            logging.debug(ET.tostring(contesttree, pretty_print=True))

        contest_name = tree[0].text
        for old, new in replacements:
            contest_name = contest_name.replace(old, new)

        # hmm - this won't work in primary, when there are multiple
        # contests per election, one for each party
        contest, created = models.Contest.objects.get_or_create(name=contest_name.strip())
        ab_cb = models.ContestBatch.objects.create(contest=contest, batch=absentee_batch)
        ev_cb = models.ContestBatch.objects.create(contest=contest, batch=early_batch)
        el_cb = models.ContestBatch.objects.create(contest=contest, batch=election_batch)

        over, created = models.Choice.objects.get_or_create(name="Over", contest=contest)
        under, created = models.Choice.objects.get_or_create(name="Under", contest=contest)

        logging.debug("Contest: %s (%s)" % (contest, tree[0].text))

        """
        We don't need the Header: we get contest from the node itself
        tree_head = extract_values(contesttree.xpath(
		                 'FormattedArea[@Type="Header"]' ),
                                fields )
        or maybe look at just '{@district_info}': 'Contest',
        if tree_head['Contest'] != tree[0].text:
            print "head = ", tree_head, " contest = ", tree[0].text
        """

        
        #logging.debug("tree:\n" + ET.tostring(contesttree, pretty_print=True))

        # Get undervotes and overvotes from Footer
        absenteer = extract_values(
            contesttree.xpath('FormattedArea[@Type="Footer"]' ),
            { '{@_Combine_Under}': 'Under',	# Report combined AB/Early here
              '{@AB_Under_votes}': 'Under',
              '{@_Combine_Over}': 'Over',	# Report combined AB/Early here
              '{@AB_Over_Votes}': 'Over' } )

        v = models.VoteCount.objects.create(choice=over, votes=absenteer['Over'], contest_batch=ab_cb)
        v = models.VoteCount.objects.create(choice=under, votes=absenteer['Under'], contest_batch=ab_cb)

        earlyr = extract_values(
            contesttree.xpath('FormattedArea[@Type="Footer"]' ),
            { '{@EA_Under_Votes}': 'Under',
              '{@EA_Over_Votes}': 'Over' } )

        v = models.VoteCount.objects.create(choice=over, votes=earlyr['Over'], contest_batch=ev_cb)
        v = models.VoteCount.objects.create(choice=under, votes=earlyr['Under'], contest_batch=ev_cb)
        electionr = extract_values(
            contesttree.xpath('FormattedArea[@Type="Footer"]' ),
            { '{sp_cumulative_rpt.c_under_votes_election}': 'Under',
              '{sp_cumulative_rpt.c_over_votes_election}': 'Over' } )

        v = models.VoteCount.objects.create(choice=over, votes=electionr['Over'], contest_batch=el_cb)
        v = models.VoteCount.objects.create(choice=under, votes=electionr['Under'], contest_batch=el_cb)
        #logging.debug(contesttree.getchildren())

        parties = set()
        # For each candidate or option
        for c in contesttree.xpath('.//FormattedAreaPair[@Type="Details"]'):
            cv = extract_values(
                c,
                { '{@_Display_Candidate_Name}': 'Name',
                  '{sp_cumulative_rpt.party}': 'Party',
                  #'{@Tl_total_cand}': 'Election day',  #??
                  '{sp_cumulative_rpt.c_votes_election}': 'Election day', #??
                  '{@_Combine_AB_EA}': 'Absentee', # report combined here
                  '{@AB_Votes}': 'Absentee',
                  '{@EA_Votes}': 'Early' } )

            logging.debug("candidate: %s" % cv['Name'])
            choice, created = models.Choice.objects.get_or_create(name=cv['Name'], contest=contest)
            absenteer.update({cv['Name']: cv['Absentee']})
            v = models.VoteCount.objects.create(choice=choice, votes=absenteer[cv['Name']], contest_batch=ab_cb)
            earlyr.update({cv['Name']: cv['Early']})
            v = models.VoteCount.objects.create(choice=choice, votes=earlyr[cv['Name']], contest_batch=ev_cb)
            electionr.update({cv['Name']: cv['Election day']})
            v = models.VoteCount.objects.create(choice=choice, votes=electionr[cv['Name']], contest_batch=el_cb)

            parties.add(cv['Party'])

        assert len(parties) > 0		# or == 1 for primary?
        party = parties.pop() or ""

        key = "%s:%s" % (contest, party)

        values[key] = [absenteer, earlyr, electionr]

    return values

def extract_values(tree, fields):
    """Extract the values of any field listed in fields from given tree"""

    if len(tree) != 1:
        logging.error("Error: tree len should be 1, not %d" % (len(tree)))
        #logging.error("Error: tree len should be 1, not %d.  Line %d" % (len(tree), tree.sourceline))
        return

    logging.debug("tree = %s, line %s" % (tree[0].tag, tree[0].sourceline))

    tree = tree[0]

    values = {}
    for i in tree.xpath('.//FormattedReportObject'):
        #logging.debug("i = %s" % (i))
        #logging.debug("i = %s, line %s" % (i[1].tag, i[1].sourceline))
        if 'FieldName' in i.attrib and i.attrib['FieldName'] in fields.keys():
            values[fields[i.attrib['FieldName']]] = i[1].text

    logging.debug("values for %s = %s" % (fields, values))
    return values

def make_audit_unit(totals, newtotals, options):
    """Subtract totals from newtotals and report the results for one audit unit.
    Sample of totals: {contest1: [AB, EV, EL], c2: [AB, EV, EL] }
     where e.g. AB = {'Under': 14, 'John': 23}
    """

    import pprint

    #pprint.pprint(newtotals)

    if options.subtract and totals == {}:	# skip first time around
        return

    for contest in sorted(newtotals):
        if options.contest != None and options.contest != contest:
            continue
        if options.subtract:
            if contest in totals:
                for n, o in zip(newtotals[contest], totals[contest]):
                    printf(contest)
                    for f in sorted(n):
                        printf("	%s	%s" % (f[0:6], int(n[f]) - int(o[f])))
                    printf('\n')

        else:
            print contest
            
            for n in newtotals[contest]:
                print "---"
                for f in sorted(n):
                    print("	%s	%s" % (n[f], f))

def printf(string):
    sys.stdout.write(string)

if __name__ == "__main__":
    main(parser)
