"""parse_swdb: parse a dbf file from the California State-wide Database (swdb):
http://swdb.berkeley.edu/

TODO:
deal with dependencies on dbfpy and openanything

file is e.g. "c023_g08_sov_data_by_g08_svprec.dbf"

Code fields:
 SVPREC precinct

 PRSxxx	president, xxx = party
 SENxxx senate, xxx = party
 CNGyyxxx	congress, district = yy, party = xxx
 ASSyyxxx assemblyman, district = yy, party = xxx
 PR_xxx_w  proposition xxx, w = y or n

 xxxVOTE by party and TOT voters
 xxxREG  by party and TOT registered
 xxDIST shows which assemblyman, state senate or congressional discrict?

Database fields are the same, except district numbers are left out.
Each precinct has only one value for each district, which is indicated
in xxDIST fields.

Special precincts (SVPREC values):
  CNTYTOT	40701	21230
  AD01_TOT	40701	21230
  CD01_TOT	40701	21230
  SD02_TOT	40701	21230
  SOVTOT	40701	21230
  SOV_CD01	0	0
  SOV_SD02	0	0
  SOV_AD01	0	0
  SOV_AD00	0	0
  SOV_CD00	0	0
  SOV_SD00	0	0
"""

import sys
sys.path.append('/home0/neal/py-tj/dbfpy/dbfpy-2.2.4')
from dbfpy.dbf import Dbf

import electionaudits.util as util
from django.db import transaction

__author__ = "Neal McBurnett <http://neal.mcburnett.org/>"
__copyright__ = "Copyright (c) 2009 Neal McBurnett"
__license__ = "MIT"

@transaction.commit_on_success
def parse_swdb(file, options):
    """Parse swdb file.
    "file" can be a file, url, or string suitable for openAnything().
    Also needs a source of the "codes" to annotate the choice names.
    """

    one_contest_prefixes = ('PRS', 'SEN', 'PR_')
    dist_contest_prefixes = ('CNG', 'ASS')
    contest_prefixes = one_contest_prefixes + dist_contest_prefixes

    """
    choices = {}
    totals = {}

    codes_name = "003.codes"
    codes = openanything.openAnything(codes_name)
    for l in codes:
        (code, choice, total) = l.rstrip().split('\t')
        if code.startswith(contest_prefixes):
            choices[code] = choice
            totals[code] = total

        elif code.endswith(('VOTE', 'REG', 'DIST')):
            # FIXME - deal with this later
            continue

        else:
            print "unrecognized code: %s in line %s" % (code, l)
    """

    reader = Dbf(file)

    au = util.AuditUnit(options.election)

    for r in reader:
        batch = r["SVPREC"]
        if batch.startswith('SOV') or batch.endswith('TOT'):
            continue

        # state-wide data marks absentee with trailing "A",
        # county data marks them with "_A"
        if batch.endswith('A'):
            type = "AB"
            if batch.endswith('_A'):
                batch = batch[0:-2]
            else:
                batch = batch[0:-1]
        else:
            type = "BA"

        addist = r['ADDIST']
        cddist = r['CDDIST']
        #sddist = r['SDDIST']

        for code in reader.fieldNames:
            if code.endswith(('PREC', 'VOTE', 'REG', 'DIST')):
                continue

            code_full = code
            contest = code[:3]
            if  code.startswith('ASS'):
                code_full = code[:3] + ("%02d" % addist) + code[-3:]
                contest = code_full[:5]
            elif  code.startswith('CNG'):
                code_full = code[:3] + ("%02d" % cddist) + code[-3:]
                contest = code_full[:5]
            elif  code.startswith('PR_'):
                contest = code[:-1]
            else:
                contest = code[:3]

            # until we fully figure out how to get the district numbers...
            # contest = contests[code]

            try:
                au = util.AuditUnit(options.election, contest, type, batch)
                au.update(code_full[len(contest):], str(r[code]))
                util.pushAuditUnit(au, min_ballots = options.min_ballots)
            except:
                print "Error looking up code %s (%s) for %s-%s" % (code, code_full, batch, type)
                continue
