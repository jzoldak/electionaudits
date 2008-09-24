#!/usr/bin/env python
"""Produce a report of audit units from incremental output of Hart Tally

%InsertOptionParserUsage%

Example:
 makeauditunits cumulative-pe-s23-b005-m800.xml cumulative-pe-s24-b006-m803.xml cumulative-pe-s25-b007-m804.xml

Use pydoc to produce full documentation.

Components:
 django apps:
   election_audit
    with parse_data util
 testdata

Questions:
 How to add info to auto-usage message about file arguments

Todo:
 Deal with namespace issues - auto-edit file, or handle it.
 Use filenames for audit unit names

 Improve documentation
 Track unrecornized FormattedValue fields - dump FieldName, value and line
 Add ballot counts (optional?) based on info box
 Put contest abbreviation in a new field, option to print with it or not

 Add support for confidence levels, etc

 Package up, as an egg?  Test on windows

 Need a way to sort DRE results out separately
 Print "few" rather than a number less than 3?
 ?Option to either produce raw report, or combined to allow publication
 Encapsulate election-specific data in specific classes
   including replacements, fields of relevance, etc
   some day: based on "programming" data from Hart system?

 Auto-sort result files, check for non-incremental results
 Check for results that list different candidates for a contest
 Look for suspicious audit units, anomalous results
 Look for columns that don't agree with previous result

 Provide interface for interactive abbreviation of contest names?

Django implementation:
 class Contest - model
  margin
  # one-to-many with Results pointed to by them
 class IncrementalResult
  contest
  early [under, over, choice_a, choice_b]
  election [under, over, choice_a, choice_b]
  generate_results

 class PublicView
  contest
 class RawView
"""

import os
import sys
import optparse
import logging
import lxml.etree as ET

from datetime import datetime

__author__ = "Neal McBurnett <http://mcburnett.org/neal/>"
__version__ = "0.3.0"
__date__ = "2008-09-08"
__copyright__ = "Copyright (c) 2008 Neal McBurnett"
__license__ = "GPL v3"

class Result:
    """
    The results for a single audit unit, along with associated info

    Usage: r = Result(dict)             # how to distinguish cum from actual
           r.update(dict)
           r.checkin()  # validate, link to appropriate contest
    def __str__(self):  #or unicode?
    need to be able to do diffs between cum Results to generate actual

    how to store them: array with columns addressed by key?

        # TODO: if not there yet, put names into contest instance,
        #  and establish order that the Results should be stored

    """

    """ earlier...    ?based on GenericResult (dynamically created somehow, add choices)?

    def __init__(self):
  contest
  audit_unit
  under, over
  choice_a, choice_b....
 Clever enumerating?  to return over, under, then each candidate
 """

    def update(self):
        """like a dictionary update, but error if value is already there"""

replacements = [
    ("THE EARNINGS FROM THE INVESTMENT", "ST VRAIN VALLEY SCHOOL DISTRICT NO. RE-1J  BALLOT ISSUE NO. 3B"),
    ("ST VRAIN SCHOOL DISTRICT", "ST VRAIN SD"),
    ("FIRE PROTECTION DISTRICT", "FPD"),
    ("REPRESENTATIVE TO THE 111th UNITED STATES CONGRESS - DISTRICT ", "CD"),
    ("REPRESENTATIVE TO THE 111TH UNITED STATES CONGRESS - DISTRICT ", "CD"),
    (", Vote For 1", ""),
    ("STATE REPRESENTATIVE - DISTRICT ", "SRD"),
    ("STATE SENATE - DISTRICT ", "SSD"),
    ("REGENT OF THE UNIVERSITY OF COLORADO CONGRESSIONAL DISTRICT ", "REGENT D"),
    ("REGENT - UNIVERSITY OF COLORADO CONGRESSIONAL DISTRICT ", "REGENT D"),
    ("COUNTY COMMISSIONER - DISTRICT ", "CCD"),
    ("JUSTICE OF THE COLORADO SUPREME COURT", "SUPREME COURT"),
    ("DISTRICT JUDGE 20th JUDICIAL DISTRICT", "JUDGE 20th JD"),
    ("ESTES VALLEY RECREATION AND PARK DIST", "ESTES VALLEY DIST"),
    ("REGIONAL TRANSPORTATION DISTRICT DIRECTOR", "RTD"),
    ("DISTRICT ATTORNEY 20TH JUDICIAL DISTRICT", "DISTRICT ATTORNEY"),
    ("DISTRICT ATTORNEY - 20th JUDICIAL DISTRICT", "DISTRICT ATTORNEY"),
    ("AMENDMENT ", "A "),
    ("BOULDER", "B"),
    ("LAFAYETTE", "LA"),
    ("LONGMONT", "LO"),
    ("LUISVILLE", "LU"),
    ("CITY OF ", ""),
    ("TOWN OF ", ""),
    ("COUNTY ", "C"),
    ("COURT OF APPEALS ", "COURT"),
    ("BALLOT ", ""),
    ("ISSUE NO. ", "I"),
    ("ISSUE ", "I "),
    ("QUESTION NO. ", "Q"),
]


parser = optparse.OptionParser(prog="makeauditunits", version=__version__)

parser.add_option("-v", "--verbose",
                  action="store_true", default=False,
                  help="Verbose output" )

parser.add_option("-d", "--debug",
                  action="store_true", default=False,
                  help="turn on debugging output")

parser.add_option("-s", "--subtract",
                  action="store_true", default=False,
                  help="subtract each file from previous file" )

parser.add_option("-c", "--contest", dest="contest",
                  help="report on CONTEST", metavar="CONTEST")

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
        args.append("/srv/s/audittools/testdata/testcum.xml")
        logging.debug("using test file: " + args[0])

    totals = {}

    for file in args:
        newtotals = do_contests(file)
        make_audit_unit(totals, newtotals, options)
        totals = newtotals

def do_contests(file):
    """Extract relevant data from each contest in a given file"""

    root = ET.parse(file).getroot()
    logging.debug("root = %s" % root)

    values = {}

    for contesttree in root.xpath('//FormattedAreaPair[@Type="Group"]'):
        tree = contesttree.xpath('FormattedArea[@Type="Header"]//FormattedReportObject[@FieldName="{@district_info}"]/FormattedValue')
        if len(tree) != 1:
            logging.error("Error: number of Headers should be 1, not %d.  Line %d" % (len(tree), contesttree.sourceline))
            logging.debug(ET.tostring(contesttree, pretty_print=True))

        contest = tree[0].text
        for old, new in replacements:
            contest = contest.replace(old, new)

        contest = contest.strip()
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
