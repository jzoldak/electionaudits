#!/usr/bin/env python
"""Produce a report of audit units from incremental cumulative reports
made with Hart's Tally software.  Normally called via manage.py parse ...

%InsertOptionParserUsage%
"""

import os
import sys
import optparse
from optparse import make_option
import logging
import csv
from datetime import datetime

from root import settings
from django.core.management import setup_environ
setup_environ(settings)
from django.db import transaction
import electionaudits.models as models
import electionaudits.util as util

__author__ = "Neal McBurnett <http://neal.mcburnett.org/>"
__copyright__ = "Copyright (c) 2008 Neal McBurnett"
__license__ = "MIT"


usage = """Usage: manage.py parse [options] [file]....

Example:
 manage.py parse -s 001_EV_p001.xml 002_AB_p022.xml 003_ED_p015.xml"""

option_list = (
    make_option("-s", "--subtract",
                  action="store_true", default=False,
                  help="Input files are incremental snapshots.   Subtract data in each file from previous data to generate batch results" ),

    make_option("-c", "--chronological",
                  action="store_true", default=False,
                  help="Sort all file arguments by last modification time" ),

    make_option("-m", "--min_ballots", dest="min_ballots", type="int",
                  default=25,
                  help="combine audit units with less than MINIMUM contest ballots", metavar="MINIMUM"),

    make_option("--contest", dest="contest",
                  help="only process CONTEST", metavar="CONTEST"),

    make_option("-e", "--election", default="test",
                  help="the name for this ELECTION"),

    make_option("-b", "--batchid", default="",
                  help="batch identifier to append to precinct name"),

    make_option("-v", "--verbose",
                  action="store_true", default=False,
                  help="Verbose output" ),

    make_option("-d", "--debug",
                  action="store_true", default=False,
                  help="turn on debugging output"),
)

parser = optparse.OptionParser(prog="parse", usage=usage, option_list=option_list)

# incorporate OptionParser usage documentation into our docstring
__doc__ = __doc__.replace("%InsertOptionParserUsage%\n", parser.format_help())

def set_options(args):
    """Return options for parser given specified arguments.
    E.g. options = set_options(["-c", "-s"])
    """

    (options, args) = parser.parse_args(args)
    return options

def main(parser):
    """obsolete and maybe broken - using management/commands/parse.py now.
    Parse and import files into the database and report summary statistics"""

    (options, args) = parser.parse_args()

    if len(args) == 0:
        args.append(os.path.join(os.path.dirname(__file__), '../../../testdata/testcum.xml'))
        logging.debug("using test file: " + args[0])

    parse(args, options)

def parse(args, options):
    "parse the files and tally the results"

    if options.debug:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    logging.basicConfig(level=loglevel) # format='%(message)s'

    logging.debug("args = %s" % list(args))

    files = []

    for arg in args:
        if os.path.isdir(arg):
            files += [os.path.join(arg, f) for f in os.listdir(arg)]
        else:
            files.append(arg)

    if options.chronological:
         filetimes = [(os.path.getmtime(f), f) for f in files]
         logging.debug("s = %s" % list(filetimes))
         filetimes.sort()
         files = [f[1] for f in filetimes]

    logging.debug("files = %s" % list(files))

    totals = {}

    for file in files:
        logging.info("Processing %s " % file)
        if file.endswith(".xml"):
            newtotals = parse_xml_crystal(file, options)
            make_audit_unit(totals, newtotals, options)
            totals = newtotals
        elif file.endswith(".csv"):
            parse_csv(file, options)
        else:
            logging.warning("Ignoring %s - unknown extension" % file)

    util.flushPipes()

    # Update tallies on all contests, just in case
    for contest in models.Contest.objects.all():
        stats = contest.tally()

        print("%(contest)-34.34s: %(total)8d %(winnervotes)8d %(winner)-8.8s %(secondvotes)8d %(second)-8.8s  %(margin)6.2f%%" % stats)

@transaction.commit_on_success
def parse_csv(file, options):
    """Parse a csv file of election data.  The model of this format
    is the San Mateo precinct spreadsheet in "testdata/test.csv".
    If the data is to be aggregated for privacy (the default), the data
    should be sorted by batch (precinct).
    """

    election = options.election

    reader = csv.DictReader(open(file))

    au_AB = util.AuditUnit()
    au_EV = util.AuditUnit()
    au_ED = util.AuditUnit()

    for r in reader:
        batch = [r['Precinct_name'] + options.batchid]
        contest = r['Contest_title']
        if r['Party_Code']:
            contest += ":" + r['Party_Code']

        if options.contest != None and options.contest != contest:
            continue

        choice = r['candidate_name']

        if batch != au_AB.batches  or  contest != au_AB.contest:
            logging.debug("now batch '%s' contest '%s' at line %d" % (batch, contest, reader.reader.line_num))
            util.pushAuditUnit(au_AB, min_ballots = options.min_ballots)
            au_AB = util.AuditUnit(election, contest, 'AB', batch)
            util.pushAuditUnit(au_EV, min_ballots = options.min_ballots)
            au_EV = util.AuditUnit(election, contest, 'EV', batch)
            util.pushAuditUnit(au_ED, min_ballots = options.min_ballots)
            au_ED = util.AuditUnit(election, contest, 'ED', batch)
        
        au_AB.update(choice, r['absentee_votes'])
        au_EV.update(choice, r['early_votes'])
        au_ED.update(choice, r['election_votes'])
        if r['cand_seq_nbr'] == '1':	# duplicated for each candidate - silly
            au_AB.update('Under', r['absentee_under_votes'])
            au_AB.update('Over', r['absentee_over_votes'])
            au_EV.update('Under', r['early_under_votes'])
            au_EV.update('Over', r['early_over_votes'])
            au_ED.update('Under', r['election_under_votes'])
            au_ED.update('Over', r['election_over_votes'])

def parse_xml_crystal(file, options):
    """Extract relevant data from each contest in a given crystalreports xml
    file"""

    import lxml.etree as ET

    election = options.election

    if os.path.basename(file) == "cumulative.xml":
        # if it's the borind default, use alternate naming scheme:
        #  parent directory of canonical path
        batch = os.path.basename(os.path.dirname(os.path.realpath(file)))
    else:
        batch = os.path.basename(file)[0:-4] 	# trim directory and ".xml"

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
    # This is a table of fixes for what Boulder needed in the 2008 general
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
        contest = contest_name.strip()
        au_AB = util.AuditUnit(election, contest, "AB", [batch])
        au_EV = util.AuditUnit(election, contest, "EV", [batch])
        au_ED = util.AuditUnit(election, contest, "ED", [batch])

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

        au_AB.update('Under', absenteer['Under'])
        au_AB.update('Over', absenteer['Over'])

        earlyr = extract_values(
            contesttree.xpath('FormattedArea[@Type="Footer"]' ),
            { '{@EA_Under_Votes}': 'Under',
              '{@EA_Over_Votes}': 'Over' } )

        au_EV.update('Under', earlyr['Under'])
        au_EV.update('Over', earlyr['Over'])

        electionr = extract_values(
            contesttree.xpath('FormattedArea[@Type="Footer"]' ),
            { '{sp_cumulative_rpt.c_under_votes_election}': 'Under',
              '{sp_cumulative_rpt.c_over_votes_election}': 'Over' } )

        au_ED.update('Under', electionr['Under'])
        au_ED.update('Over', electionr['Over'])

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

            au_AB.update(cv['Name'], cv['Absentee'])
            au_EV.update(cv['Name'], cv['Early'])
            au_ED.update(cv['Name'], cv['Election day'])

            parties.add(cv['Party'])

        assert len(parties) > 0		# or == 1 for primary?
        party = parties.pop() or ""

        key = "%s:%s" % (contest, party)

        values[key] = [au_AB, au_EV, au_ED]

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

@transaction.commit_on_success
def make_audit_unit(totals, newtotals, options):
    """Subtract totals from newtotals and report the results for one audit unit.
    Sample of totals: {contest1: [AB, EV, ED], c2: [AB, EV, ED] }
     where e.g. AB = {'Under': 14, 'John': 23}
    """

    #import pprint
    #pprint.pprint(newtotals)

    if options.subtract and totals == {}:	# skip first time around
        return

    for contest in sorted(newtotals):
        if options.contest != None and options.contest != contest:
            continue
        if options.subtract:
            for n, o in zip(newtotals[contest], totals[contest]):
                diff = n.combine(o, subtract=True)
                util.pushAuditUnit(diff, min_ballots = options.min_ballots)

        else:
            for au in newtotals[contest]:
                util.pushAuditUnit(au, min_ballots = options.min_ballots)

def printf(string):
    sys.stdout.write(string)

if __name__ == "__main__":
    main(parser)
