#!/usr/bin/env python
"""Parse a Cast Vote Record (CVR), e.g. from an ivotronic "el155" file.
example: python parsecvr.py /srv/voting/audit/sc/colleton_co_02_01_11/colleton_co_02_01_11_el155.lst > /tmp/q3
 sort /tmp/q3|uniq -c | sort -n > /tmp/q4
"""

import sys
import re
import fileinput

def parse_el155(file, options):
    """
    Parse an ES&S Ivotronic el155 cast vote record file, like the one at
    testdata/test_el155.txt
    """

    # regexp to match record format of cast vote record file aka vote image file. This returns six named
    # values: ivo id, ballot image id, aserisk indicating ballot
    # border, candidate id, candidate name and contest name.
    # Based on Chip Moore's regular expresssions in the perl module rgex.pm

    # Example: 5120350    5 *   10 Nikki R Haley                          GOVERNOR
    ballot_record = re.compile(
        r'(?P<ivo>\d{7})\s+'
        r'(?P<ballot_image>\d+)\s+'
        r'(?P<asterisk>\*{0,1})\s+'
        r'(?P<cid>\d+)\s+'
        r'(?P<cname>\w.*?\w+)\s{2,}'
        r'(?P<rname>\w.*?\w+)'
        '\r?$' )

    # Example: RUN DATE:11/30/10 10:33 AM                         PRECINCT  101 - College                                  ELECTION ID: 40110210
    precinct_record = re.compile(
        r'RUN\sDATE:'
        r'(?P<month>\d{2})/'
        r'(?P<day>\d{2})/'
        r'(?P<year>\d{2}) '
        r'(?P<hour>\d{2}):'
        r'(?P<minute>\d{2}) '
        r'(?P<ampm>am|AM|pm|PM)\s+PRECINCT\s+'
        r'(?P<precinct>\d{1,4})\s-\s'
        r'(?P<pname>\w.*?\w+)\s{4,}ELECTION ID:\s+'
        r'(?P<eid>\d+)'
        '\r?$' )

    precinct = None
    totals = {}
    cvr = set()

    for line in fileinput.input():

        m = ballot_record.match(line)
        if m:
            cid = int(m.group('cid'))
            # print "{ivo}	{ballot_image}	{asterisk}	{cid}	{cname}	{rname}".format((), **m.groupdict())
            totals[cid] = totals.get(cid, 0) + 1

            if m.group('asterisk'):
                print "cvr =", cvr
                cvr = set()

            cvr.add(cid)
                
            """
            if m.group('rname') in cvr:
                print "ERROR: duplication: for {rname} was {existing}, now {new}".format(rname = m.group('rname'), existing = cvr[m.group('rname')], new = m.group('cid'))
            else:
                cvr[m.group('rname')] = m.group('cid')
            """

            continue

        m = precinct_record.match(line)
        if m:
            # print m.groupdict()

            if m.group('precinct') != precinct:
                precinct = m.group('precinct')
                for key, value in sorted(totals.iteritems()):
                    print key, value

                print "Precinct: {precinct}".format((), **m.groupdict())
            
            continue
    
if __name__ == "__main__":
    parse_el155(sys.argv[1], None)
