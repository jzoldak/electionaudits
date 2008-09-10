#!/usr/bin/env python
"""Produce a report of audit units from incremental output of Hart Tally

%InsertOptionParserUsage%

Example:
 makeauditunits.py cumulative-pe-s23-b005-m800.xml cumulative-pe-s24-b006-m803.xml cumulative-pe-s25-b007-m804.xml

Use pydoc to produce full documentation.

Question:
 Where are ballot counts?  Total the ballots for Senate DEM+REP or something

Todo:
 Deal with namespace issues - auto-edit file, or handle it.
 Divide results into Early and Election, only output stuff that changes
 Option to either produce raw report, or combined to allow publication
 Encapsulate election-specific data in an Election class
   including replace_dict, fields of relevance, etc
   based on "programming" data from Hart system?
 Provide interface for interactive abbreviation of contest names?
 Auto-sort result files, check for non-incremental results
 Check for results that list different candidates for a contest
 Add support for confidence levels, etc
 Look for suspicious audit units, anomalous results
 Look for columns that don't agree with previous result
 Support for selecting sequence of contests in columns
 Produce totals
 Need a way to sort DRE results out separately

Django implementation:
 Class Contest - model
  margin
  list of Results
 Class Result  based on GenericResult (dynamically created somehow, add choices)
  contest
  audit_unit
  under, over
  choice_a, choice_b....
 Class PublicView
  contest
 Class RawView

http://code.djangoproject.com/wiki/DynamicModels plus syncdb and admin magic

"""

import os
import sys
import optparse
import logging
import lxml.etree as ET

from datetime import datetime

__author__ = "Neal McBurnett <http://mcburnett.org/neal/>"
__version__ = "0.1.0"
__date__ = "2008-09-08"
__copyright__ = "Copyright (c) 2008 Neal McBurnett"
__license__ = "GPL v3"

replace_dict = {
    "REPRESENTATIVE TO THE 111th UNITED STATES CONGRESS - DISTRICT ": "CD",
    ", Vote For 1 ": "",
    "STATE REPRESENTATIVE - DISTRICT ": "SRD",
    "STATE SENATE - DISTRICT ": "SSD",
    "REGENT OF THE UNIVERSITY OF COLORADO CONGRESSIONAL DISTRICT ": "Regent D",
    "COUNTY COMMISSIONER - DISTRICT ": "CCD",
    "DISTRICT ATTORNEY - 20th JUDICIAL DISTRICT": "District Attorney",
}


parser = optparse.OptionParser(prog="makeauditunits.py", version=__version__)

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

    totals = {}
    for file in args:
        newtotals = do_contests(file)
        makeauditunit(totals, newtotals)
        totals = newtotals

def do_contests(file):
    """Extract relevant data from each contest in a given file"""

    root = ET.parse("/tmp/cumulative-pe-s23-b005-m800.xml").getroot()

    values = {}

    for contesttree in root.xpath('//FormattedAreaPair[@Type="Group"]'):
        tree = contesttree.xpath('FormattedArea[@Type="Header"]//FormattedReportObject[@FieldName="{@district_info}"]/FormattedValue')
        if len(tree) != 1:
            logging.error("Error: number of headers should be 1: %s" % (ET.tostring(contesttree, pretty_print=True)))

        contest = tree[0].text
        for key in replace_dict:
            contest = contest.replace(key, replace_dict[key])

        contest = contest.strip()
        logging.debug("Contest: %s (%s)" % (contest, tree[0].text))

        fields = {'{@_Display_Candidate_Name}': 'Name',
                  '{@district_info}': 'Contest',
                  '{sp_cumulative_rpt.party}': 'Party',
                  '{@Tl_total_cand}': 'Election day',
                  '{@_Combine_AB_EA}': 'Early/Absentee',
                  '{@_Combine_Under}': 'UnderEarly',
                  '{sp_cumulative_rpt.c_under_votes_election}': 'UnderElection',
                  '{@_Combine_Over}': 'OverEarly',
                  '{sp_cumulative_rpt.c_over_votes_election}': 'OverElection' }

        tree_head = extract_values(contesttree.xpath(
		                 'FormattedArea[@Type="Header"]' ),
                                fields )
        
        # Get undervotes and overvotes from Footer
        tree_foot = extract_values(contesttree.xpath(
		                 'FormattedArea[@Type="Footer"]' ),
                                fields )
        
        # For each candidate or option
        v = []
        logging.debug(contesttree.getchildren())
        for c in contesttree.xpath('.//FormattedAreaPair[@Type="Details"]'):
            cv = extract_values(c, fields )
            logging.debug("candidate: %s" % cv['Name'])
            v.append(cv)

        parties = [cv['Party'] for cv in v]
        tree_head.update({'Party': parties})
        key = "%s:%s" % (contest, parties)
        values[key] = [tree_foot, v]

        # For each candidate, get Election day and Early/Absentee
        # '{@_Display_Candidate_Name}': 'Name',

        # '{@district_info}': 'Contest' 
              
    return values

def extract_values(tree, fields):
    """Extract values from given tree for fields"""

    """Return results as [ [headers...] [Early...]  [Election]]"""

    logging.debug("tree = %s, line %s" % (tree[0].tag, tree[0].sourceline))
    # "fields = %s" % fields

    if len(tree) != 1:
        print "Error: number of headers should be 1, not %d.  Line %d" % (len(tree), tree[0].sourceline)

    tree = tree[0]

    values = {}
    for i in tree.xpath('.//FormattedReportObject'):
        #logging.debug("i = %s" % (i))
        logging.debug("i = %s, line %s" % (i[1].tag, i[1].sourceline))
        if 'FieldName' in i.attrib and i.attrib['FieldName'] in fields.keys():
            values[fields[i.attrib['FieldName']]] = i[1].text

    logging.debug("values = %s" % values)
    return values

def makeauditunit(totals, newtotals):
    """Subtract totals from newtotals and report the results for one audit unit"""

    import pprint
    pprint.pprint(newtotals)

if __name__ == "__main__":
    main(parser)
