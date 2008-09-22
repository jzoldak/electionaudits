#!/usr/bin/env python
"""Produce a report of audit units from incremental output of Hart Tally

%InsertOptionParserUsage%

Example:
 makeauditunits cumulative-pe-s23-b005-m800.xml cumulative-pe-s24-b006-m803.xml cumulative-pe-s25-b007-m804.xml

Use pydoc to produce full documentation.

Question:
 Where are ballot counts?  Total the ballots for Senate DEM+REP or something

Todo:
 Separate "Early" from "Absentee", report both
 Subtract to produce audit batch totals
 Deal with namespace issues - auto-edit file, or handle it.
 Add support for confidence levels, etc

 Need a way to sort DRE results out separately
 Divide results into Early and Election, only output stuff that changes
 Print "few" rather than a number less than 3?
 Option to either produce raw report, or combined to allow publication
 Encapsulate election-specific data in an Election class
   including replace_dict, fields of relevance, etc
   some day: based on "programming" data from Hart system?
 Provide interface for interactive abbreviation of contest names?
 Auto-sort result files, check for non-incremental results
 Check for results that list different candidates for a contest
 Look for suspicious audit units, anomalous results
 Look for columns that don't agree with previous result
 Support for selecting sequence of contests in columns

 How to add info to auto-usage message about file arguments

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

http://code.djangoproject.com/wiki/DynamicModels plus syncdb and admin magic

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

replace_dict = {
    "REPRESENTATIVE TO THE 111th UNITED STATES CONGRESS - DISTRICT ": "CD",
    "REPRESENTATIVE TO THE 111TH UNITED STATES CONGRESS - DISTRICT ": "CD",
    ", Vote For 1": "",
    "STATE REPRESENTATIVE - DISTRICT ": "SRD",
    "STATE SENATE - DISTRICT ": "SSD",
    "REGENT OF THE UNIVERSITY OF COLORADO CONGRESSIONAL DISTRICT ": "Regent D",
    "COUNTY COMMISSIONER - DISTRICT ": "CCD",
    "DISTRICT ATTORNEY - 20th JUDICIAL DISTRICT": "District Attorney",
}


parser = optparse.OptionParser(prog="makeauditunits", version=__version__)

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

    totals = {}

    if len(args) == 0:
        args.append("/srv/s/audittools/testcum.xml")
        logging.debug("using test file: " + args[0])

    for file in args:
        newtotals = do_contests(file)
        make_audit_unit(totals, newtotals)
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
        for key in replace_dict:
            contest = contest.replace(key, replace_dict[key])

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
        party = parties.pop()

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

def make_audit_unit(totals, newtotals):
    """Subtract totals from newtotals and report the results for one audit unit"""

    import pprint

    #pprint.pprint(newtotals)

    for contest in sorted(newtotals):
        print contest
        for x in newtotals[contest]:
            print "---"
            for f in x:
                print("	%s	%s" % (x[f], f)) # - totals[contest][x][f])


if __name__ == "__main__":
    main(parser)


    """
    to test: ./makeauditunits.py > /tmp/q;  diff /tmp/q testcum.out

    to profile:
      python -m cProfile -s time makeauditunits.py 2>&1 > profile-0.3.0

     or

    import cProfile
    cProfile.run('main(parser)')

    or older:

    import hotshot, hotshot.stats
    prof = hotshot.Profile("test.prof")
    #benchtime, stones = prof.runcall(test.pystone.pystones)
    benchtime, stones = prof.runcall(main(parser))
    prof.close()
    stats = hotshot.stats.load("stones.prof")
    stats.strip_dirs()
    stats.sort_stats('time', 'calls')
    stats.print_stats(20)
    """

    """
    extras
    tree = contesttree.xpath('FormattedArea[@Type="Header"]//FormattedReportObject[@FieldName="{@Contest Title}"]/FormattedValue')
    """

"""
Fields in the 08 general election  cumulative report from crystal
1043974 2008-09-22 12:22 cumulative.xml

# grep Field cumulative.xml| sed -e 's/^.*FieldN/FieldN/' -e 's,><ObjectName>.*,,' | sort|uniq -c|sort -n 
     71 FieldName="{@AB_Over_Votes}"
     71 FieldName="{@AB_Per_absentee_over}"
     71 FieldName="{@AB_Per_absentee_total}"
     71 FieldName="{@AB_Per_absentee_under}"
     71 FieldName="{@AB_Total_absentee}"
     71 FieldName="{@AB_Under_votes}"
     71 FieldName="{@ballots_cast}"
     71 FieldName="{@district_info}"
     71 FieldName="{@EA_Over_Votes}"
     71 FieldName="{@Ea_Per_early_over}"
     71 FieldName="{@Ea_Per_early_total}"
     71 FieldName="{@Ea_Per_early_under}"
     71 FieldName="{@EA_Total}"
     71 FieldName="{@EA_Under_Votes}"
     71 FieldName="{@El_Per_elect_over}"
     71 FieldName="{@El_Per_elect_total}"
     71 FieldName="{@El_Per_elect_under}"
     71 FieldName="{sp_cumulative_rpt.counted_precincts}"
     71 FieldName="{sp_cumulative_rpt.c_over_votes_election}"
     71 FieldName="{sp_cumulative_rpt.c_under_votes_election}"
     71 FieldName="{sp_cumulative_rpt.reg_voters}"
     71 FieldName="{sp_cumulative_rpt.total_precincts}"
     71 FieldName="{@Tl_Per_over}"
     71 FieldName="{@Tl_Per_Total}"
     71 FieldName="{@Tl_Per_under}"
     71 FieldName="{@Tl_total_over}"
     71 FieldName="{@Tl_total_under}"
     71 FieldName="{@Tl_total_votes}"
     71 FieldName="{@To_Percent_Turnout}"
     71 FieldName="{@To_Per_Precinct_Reporting}"
     71 FieldName="{#total_election}"
    159 FieldName="{@Ab_Per_absentee_cand}"
    159 FieldName="{@AB_Votes}"
    159 FieldName="{@_Display_Candidate_Name}"
    159 FieldName="{@Ea_Per_early_cand}"
    159 FieldName="{@EA_Votes}"
    159 FieldName="{@El_Per_elect_cand}"
    159 FieldName="{sp_cumulative_rpt.c_votes_election}"
    159 FieldName="{sp_cumulative_rpt.party}"
    159 FieldName="{@Tl_Per_cand}"
    159 FieldName="{@Tl_total_cand}"

cat /srv/s/audittools/testcum.xml | grep Field | sed -e 's/^.*FieldN/FieldN/' -e 's,><ObjectName>.*,,' | sort|uniq -c|sort -n 
     31 FieldName="{@_Combine_El_Per_elect_over}"
     31 FieldName="{@_Combine_El_Per_elect_under}"
     31 FieldName="{@_Combine_Over}"
     31 FieldName="{@_Combine_Percent_Over}"
     31 FieldName="{@_Combine_Percent_Under}"
     31 FieldName="{@_Combine_Tl_Per_Over}"
     31 FieldName="{@_Combine_Tl_Per_Under}"
     31 FieldName="{@_Combine_Under}"
     31 FieldName="{sp_cumulative_rpt.c_over_votes_election}"
     31 FieldName="{sp_cumulative_rpt.c_under_votes_election}"
     31 FieldName="{@Tl_total_over}"
     31 FieldName="{@Tl_total_under}"
     34 FieldName="{@_Combine_AB_EA_Total}"
     34 FieldName="{@_Combine_El_Per_elect_total}"
     34 FieldName="{@_Combine_Percent_Cast}"
     34 FieldName="{@_Combine_Tl_Per_Total}"
     34 FieldName="{@district_info}"
     34 FieldName="{@Tl_total_votes}"
     34 FieldName="{#total_election}"
     37 FieldName="{@_Combine_AB_EA}"
     37 FieldName="{@_Combine%_AB_EA}"
     37 FieldName="{@_Combine_El_Per_elect_cand}"
     37 FieldName="{@_Combine_Tl_Per_cand}"
     37 FieldName="{@_Display_Candidate_Name}"
     37 FieldName="{sp_cumulative_rpt.c_votes_election}"
     37 FieldName="{sp_cumulative_rpt.party}"
     37 FieldName="{@Tl_total_cand}"


Fields in a Canvass report, by frequency:
   4566  FieldName="GroupName ({sp_tly_precinct_rpt.pct_seq_nbr})"
   4566  FieldName="{@Turn_Out%}"
   4566  FieldName="{@Total_Cand_2_Show}"
   4566  FieldName="{@Total_Cand_1_Show}"
   4566  FieldName="Maximum ({@Total_Ballots}, {sp_tly_precinct_rpt.pct_seq_nbr})"
   4566  FieldName="Maximum ({sp_tly_precinct_rpt.ballots_election}, {sp_tly_precinct_rpt.pct_seq_nbr})"
   4566  FieldName="Maximum ({sp_tly_precinct_rpt.ballots_early}, {sp_tly_precinct_rpt.pct_seq_nbr})"
   4566  FieldName="Maximum ({sp_tly_precinct_rpt.ballots_absentee}, {sp_tly_precinct_rpt.pct_seq_nbr})"
   4566  FieldName="Maximum ({@Reg_Voters}, {sp_tly_precinct_rpt.pct_seq_nbr})"
    283  FieldName="{@Total_Cand_3_Show}"
    174  FieldName="{@Total_Cand_4_Show}"
     34  FieldName="{@_Parse_Cand_2}"
     34  FieldName="{@_Parse_Cand_1}"
     34  FieldName="{@Continued}"
     34  FieldName="{@Contest Title}"
     34  FieldName="{@Total_RaceCand_2_Show}"
     34  FieldName="{@Total_RaceCand_1_Show}"
     34  FieldName="Sum ({@Total_Ballots}, {sp_tly_precinct_rpt.race_seq_nbr})"
     34  FieldName="Sum ({sp_tly_precinct_rpt.ballots_election}, {sp_tly_precinct_rpt.race_seq_nbr})"
     34  FieldName="Sum ({sp_tly_precinct_rpt.ballots_early}, {sp_tly_precinct_rpt.race_seq_nbr})"
     34  FieldName="Sum ({sp_tly_precinct_rpt.ballots_absentee}, {sp_tly_precinct_rpt.race_seq_nbr})"
     34  FieldName="Sum ({@Reg_Voters}, {sp_tly_precinct_rpt.race_seq_nbr})"
      2  FieldName="{@_Parse_Cand_3}"
      2  FieldName="{@Total_RaceCand_3_Show}"
      1  FieldName="{@_Parse_Cand_4}"
      1  FieldName="{@Total_RaceCand_4_Show}"
"""
