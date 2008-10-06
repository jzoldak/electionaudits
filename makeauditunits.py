#!/usr/bin/env python
"""Produce a report of audit units from incremental cumulative reports
made with Hart's Tally software.

%InsertOptionParserUsage%

Example:
 Currently, you first need to make sure that makeauditunits knows
 how to save the changes in the database i.e. which settings to use.  E.g.
 $ export DJANGO_SETTINGS_MODULE=audittools.settings

 $ makeauditunits -s cumulative-pe-s23-b005-m800.xml cumulative-pe-s24-b006-m803.xml cumulative-pe-s25-b007-m804.xml

"""

import os
import sys
import optparse
import logging
import csv
import lxml.etree as ET

import electionaudit.models as models
from django.db import transaction

from datetime import datetime

__author__ = "Neal McBurnett <http://mcburnett.org/neal/>"
__version__ = "0.6.0"
__date__ = "2008-09-08"
__copyright__ = "Copyright (c) 2008 Neal McBurnett"
__license__ = "GPL v3"

parser = optparse.OptionParser(prog="makeauditunits", version=__version__)

parser.add_option("-s", "--subtract",
                  action="store_true", default=False,
                  help="Input files are incremental snapshots.   Subtract data in each file from previous data to generate batch results" )

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

    for file in args:
        if file.endswith(".xml"):
            newtotals = parse_xml_crystal(file)
            make_audit_unit(totals, newtotals, options)
            totals = newtotals
        elif file.endswith(".csv"):
            parse_csv(file)

    # Update tallies on all contests, just in case
    for contest in models.Contest.objects.all():
        contest.tally()

@transaction.commit_manually
def parse_csv(file):
    """Parse a csv file of election data.  The model of this format
    is the San Mateo precinct spreadsheet in testdata/test.csv"""

    from django.core.management import setup_environ
    from audittools import settings

    setup_environ(settings)

    election = os.path.basename(file)[0:-4]

    reader = csv.DictReader(open(file))

    oldbatch = ''

    for r in reader:
        batch = r['Precinct_name']
        if batch != oldbatch:
            oldbatch = batch
            print "commit new batch:", batch
            transaction.commit()

        contest = r['Contest_title']
        if r['Party_Code']:
            contest += ":" + r['Party_Code']
        choice = r['candidate_name']
        
        new_contest_batch(election, batch, contest, choice, 'AB', r['absentee_votes'])
        new_contest_batch(election, batch, contest, choice, 'EL', r['election_votes'])
        if r['cand_seq_nbr'] == '1':	# duplicated for each candidate - silly
            new_contest_batch(election, batch, contest, 'Under', 'AB', r['absentee_under_votes'])
            new_contest_batch(election, batch, contest, 'Over',  'AB', r['absentee_over_votes'])
            new_contest_batch(election, batch, contest, 'Under', 'EL', r['election_under_votes'])
            new_contest_batch(election, batch, contest, 'Over',  'EL', r['election_over_votes'])

    transaction.commit()
            
def new_contest_batch(election, batch, contest, choice, type, votes):
    election, created = models.CountyElection.objects.get_or_create(name=election)
    batch, created = models.Batch.objects.get_or_create(name=batch, election=election, type=type )
    contest, created = models.Contest.objects.get_or_create(name=contest)
    contest_batch, created = models.ContestBatch.objects.get_or_create(contest=contest, batch=batch)
    choice, created = models.Choice.objects.get_or_create(name=choice, contest=contest)
    models.VoteCount.objects.create(choice=choice, votes=votes, contest_batch=contest_batch)

@transaction.commit_on_success
def parse_xml_crystal(file):
    """Extract relevant data from each contest in a given crystalreports xml
    file"""

    from django.core.management import setup_environ
    from audittools import settings

    setup_environ(settings)

    election, created = models.CountyElection.objects.get_or_create(name="BoulderGeneral")
    absentee_batch, created = models.Batch.objects.get_or_create(
        name=os.path.basename(file)[0:-4],	# trim directory and ".xml"
        election=election,
        type="AB" )

    root = ET.parse(file).getroot()
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
        contest_batch = models.ContestBatch.objects.create(contest=contest, batch=absentee_batch)

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

        v = models.VoteCount.objects.create(choice=over, votes=absenteer['Over'], contest_batch=contest_batch)
        v = models.VoteCount.objects.create(choice=under, votes=absenteer['Under'], contest_batch=contest_batch)

        earlyr = extract_values(
            contesttree.xpath('FormattedArea[@Type="Footer"]' ),
            { '{@EA_Under_Votes}': 'Under',
              '{@EA_Over_Votes}': 'Over' } )

        electionr = extract_values(
            contesttree.xpath('FormattedArea[@Type="Footer"]' ),
            { '{sp_cumulative_rpt.c_under_votes_election}': 'Under',
              '{sp_cumulative_rpt.c_over_votes_election}': 'Over' } )

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
            absenteer.update({cv['Name']: cv['Absentee']})
            choice, created = models.Choice.objects.get_or_create(name=cv['Name'], contest=contest)
            v = models.VoteCount.objects.create(choice=choice, votes=absenteer[cv['Name']], contest_batch=contest_batch)
            earlyr.update({cv['Name']: cv['Early']})
            electionr.update({cv['Name']: cv['Election day']})
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
    """Subtract totals from newtotals and report the results for one audit unit"""

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
