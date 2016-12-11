#!/usr/bin/python

import sys
import fileinput
import csv

def parse_csv(file, options):
    """Parse handcount data from Boulder spreadsheet into clean tab-separated-values
    Model is the "CountEntry" spreadsheet produced in the
    2010 Boulder audits, converted to a set of csv files by ssconvert.py
    Confused a bit by the fact that some headers are above
    the field they label (Audit Batch ID and Option...)
    and some to the left of it (Contest)

    Skip or ignore the "Entry Master" sheet.

    "Contest:","COUNTY ISSUE 1B [Countywide Open Space Sales and Use Tax Increase and Bond Authorization] Vote For 1",,,,,,,,,,
    ....
    "Audit Batch ID","System ID","Batch Number",,"Date","Count #",,,,,,
    "p300_mb_451",,,,,1,,,,,,
    ....
    "Option","Total 1","Total 2","Total 3","Total 4","Total 5","Total 6","Total 7","Total 8","MVW Count","Machine Count","Diff"
    "YES",59,24,38,17,,,,,138,138,0
    ....
    """

    #election = options.election

    parseCounts = False
    parseBatch = False
    contest = "_unknown_"
    batch = "_unknown_"

    for line in fileinput.input(file):
        fields = line.strip().split(',')

        if fields[0] == '"Contest:"':
            contest = fields[1]
        elif fields[0] == '"Option"':
            parseCounts = True
        elif fields[0] == '"Group Totals"':
            parseCounts = False
        elif fields[0] == '"Audit Batch ID"':
            parseBatch = True
            continue

        if parseBatch:
            batch = fields[0]
            parseBatch = False
            continue

        if parseCounts:
            # print diff, machine count, choice, batch, contest, filename
            print "%s\t%s\t%s\t%s\t%s\t%s" % (fields[11], fields[10], fields[0], batch, contest, fileinput.filename())

if __name__ == "__main__":
    parse_csv(sys.argv[1:], None)
