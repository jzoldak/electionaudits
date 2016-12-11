import os
from django.test import TestCase
from electionaudits.management.commands.parse import Command
import electionaudits.parsers
import electionaudits.models as models

class TestCaseDiff(TestCase):
    "Provide failDiffUnlessEqual function for derived classes"

    def failDiffUnlessEqual(self, file1, string2, testname):
        """Like failUnlessEqual, but compares contents of file file1 to string2
        and shows diffs in context, labeled with testname.
        """

        string1 = open(file1).read()

        if string1 != string2:
            import tempfile
            (savenew, name) = tempfile.mkstemp(suffix=".html")
            os.write(savenew, string2)
            os.close(savenew)
            print "\nNew %s output saved in %s" % (testname, name)
            print "diff %s %s\n" % (file1, name)

            import difflib
            s1=string1.split('\n')
            s2=string2.split('\n')
            #hd = difflib.HtmlDiff()
            #os.write(savenew, "Diff:\n" + hd.make_file(s1, s2))

            # import pdb; pdb.set_trace()	# put this where you want to start manual debugging via pdb

            self.failUnlessEqual(string1, string2,
                                 testname + " content differs:\n" +
                                 '\n'.join(difflib.unified_diff(s1, s2) ))

class TestT0(TestCaseDiff):
    def test_reports(self):
        "TestT0: Load testdata/t0/* and verify /reports/ /reports/1/ /selections/ /selections/4/ /results/ and /results/ after selections."

        response = self.client.get('/reports/')
        self.failUnlessEqual(response.status_code, 200)
        
        c = Command()
        options = electionaudits.parsers.set_options(["-c", "-s"])
        c.handle("../testdata/t0", **options.__dict__)

        response = self.client.get('/reports/')
        self.failUnlessEqual(response.status_code, 200)
        self.failDiffUnlessEqual("../testdata/t0/reports.html", response.content, "/reports/")

        response = self.client.get('/reports/1/')
        self.failUnlessEqual(response.status_code, 200)
        self.failDiffUnlessEqual("../testdata/t0/report.html", response.content, "/reports/1/")

        election = models.CountyElection.objects.get(id=1)
        election.random_seed = "123456789012345"
        election.save()

        response = self.client.get('/selections/')
        self.failUnlessEqual(response.status_code, 200)
        self.failDiffUnlessEqual("../testdata/t0/selections.html", response.content, "/reports/")

        response = self.client.get('/selections/4/')
        self.failUnlessEqual(response.status_code, 200)
        self.failDiffUnlessEqual("../testdata/t0/selections-4.html", response.content, "/reports/1/")

        response = self.client.get('/results/')
        self.failUnlessEqual(response.status_code, 200)
        self.failDiffUnlessEqual("../testdata/t0/results0.html", response.content, "/results/")

        for contest_id in [4]: # REPRESENTATIVE TO THE 111TH UNITED STATES CONGRESS - DISTRICT 4
            contest = models.Contest.objects.get(id=contest_id)
            contest.selected=True
            contest.save()

        for contest_id in [7]:  # STATE SENATE - DISTRICT 17 - should be only one contestbatch for that
            au = models.ContestBatch.objects.get(contest=contest_id)
            au.selected=True
            au.save()

        response = self.client.get('/results/')
        self.failUnlessEqual(response.status_code, 200)
        self.failDiffUnlessEqual("../testdata/t0/results.html", response.content, "/results/")

    def test_stats(self):
        "Try /stats/"

        response = self.client.get('/stats/')
        self.failUnlessEqual(response.status_code, 200)

class TestCsv(TestCaseDiff):
    def test_csv(self):
        "TestCsv: Try parsing san mateo csv data and comparing tally() output"

        statdir = {u'PROPOSITION 92':
                       {'contest': u'PROPOSITION 92', 'secondvotes': 46443, 'winner': u'NO', 'second': u'YES', 'winnervotes': 69468, 'total': 124848, 'margin': 18.442425990003844},
                   u'PRESIDENT OF THE UNITED STATES:DEM':
                       {'contest': u'PRESIDENT OF THE UNITED STATES:DEM', 'secondvotes': 27303, 'winner': u'HILLARY CLINTON', 'second': u'BARACK OBAMA', 'winnervotes': 36818, 'total': 70352, 'margin': 13.524846486240619}
                   }

        c = Command()
        options = electionaudits.parsers.set_options([])
        c.handle("../testdata/test-san-mateo-dp-92-p.csv", **options.__dict__)

        for contest in models.Contest.objects.all():
            stats = contest.tally()
            prevstats = statdir[stats['contest']]
            for k, v in stats.iteritems():
                self.failUnlessEqual(v, prevstats[k])


class TestBoulderCsv(TestCaseDiff):
    def test_csv(self):
        "TestBoulderCsv: Try parsing Boulder csv data and comparing tally() output"

        statdir = {u'COUNTY ISSUE 1B [Countywide Open Space Sales and Use Tax Increase and Bond Authorization] Vote For 1':
                       {'contest': u'COUNTY ISSUE 1B [Countywide Open Space Sales and Use Tax Increase and Bond Authorization] Vote For 1',
                        'secondvotes': 359, 'winner': u'YES', 'second': u'NO', 'winnervotes': 472, 'total': 872, 'margin': 12.958715596330276},
                   }

        c = Command()
        options = electionaudits.parsers.set_options([])
        c.handle("../testdata/test-boulder.csv", **options.__dict__)

        for contest in models.Contest.objects.all():
            stats = contest.tally()
            prevstats = statdir[stats['contest']]
            for k, v in stats.iteritems():
                self.failUnlessEqual(v, prevstats[k])


class TestSWDB_csv_KM(TestCaseDiff):
    def test_csv(self):
        "TestSWDB_csv_KM: Try parsing SWDB csv CD3 data and comparing error_bounds(), report, selections vs kaplan-example"

        prev_eb = {'U': 20.47011975018621,
                   'margins':
                       {'CNGREP': {'CNGGRN': 155424, 'CNGAIP': 155424, 'CNGLIB': 148151, 'CNGDEM': 17453, 'CNGPAF': 142046}} }

        c = Command()
        options = electionaudits.parsers.set_options(["-m 1"])
        c.handle("../testdata/test-swdb-cd3.csv", **options.__dict__)

        contest = models.Contest.objects.get(id=1)

        self.failUnlessEqual(contest.U, prev_eb['U'])

        # FIXME: figure out how to get the right margin lookups here, perhaps clearer errors
        #for choice, margin in prev_eb['margins']['CNGREP']:
        #    self.failUnlessEqual(margin, eb['margins']['CNGREP'][??])

        response = self.client.get('/kmreports/1/')
        self.failUnlessEqual(response.status_code, 200)
        self.failDiffUnlessEqual("../testdata/kmreport-1.html", response.content, "/kmreports/1/")

        contest.confidence = 75
        contest.save()

        election = models.CountyElection.objects.get(id=1)
        election.random_seed = "123456789012345"
        election.save()

        response = self.client.get('/kmresults/1/')
        self.failUnlessEqual(response.status_code, 200)
        self.failDiffUnlessEqual("../testdata/kmresult-1.html", response.content, "/kmresults/1/")


"""
first try, this prng, uploaded #'s different order: 0.098701

Testing selection against kaplan-example - need to use constants for mersenne twister selection since python seeding is different than R
            # Use this prng, and factor of 3.4, to recreate 47 random numbers from mersenne twister seed of 20100110 as generated by R, like Lindeman kaplan-example
            # prng = itertools.cycle([ 0.40827853, 0.80061871, 0.94676299, 0.49736872, 0.46192904, 0.81279404, 0.83129304, 0.16215752, 0.98246675, 0.95694084, 0.67667001, 0.60017428, 0.36931386, 0.80239029, 0.77339991, 0.03171216, 0.27891897, 0.68962453, 0.36474152, 0.68695872, 0.98093805, 0.30901657, 0.97122549, 0.76789247, 0.56631869, 0.31349720, 0.03224969, 0.49095661, 0.12090347, 0.09948674, 0.62830930, 0.10122452, 0.28973657, 0.99603961, 0.54367589, 0.12708358, 0.12108279, 0.03328502, 0.56681770, 0.82867559, 0.34289365, 0.58856273, 0.11031500, 0.27732952, 0.04791692, 0.19352317, 0.90055056 ]).next

"""
