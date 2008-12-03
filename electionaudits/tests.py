import os
from django.test import TestCase
from electionaudits.management.commands.parse import Command
import electionaudits.parsers
import electionaudits.models as models

class SimpleTest(TestCase):
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
            print "New %s output saved in %s" % (testname, name)
            print "diff %s %s" % (name, file1)

            import difflib
            s1=string1.split('\n')
            s2=string2.split('\n')
            #hd = difflib.HtmlDiff()
            #os.write(savenew, "Diff:\n" + hd.make_file(s1, s2))
            self.failUnlessEqual(string1, string2,
                                 testname + " content differs:\n" +
                                 '\n'.join(difflib.unified_diff(s1, s2) ))

    def test_reports(self):
        "Try /reports/  /reports/1/ and /results/ with testdata/t0"

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

        response = self.client.get('/selections/')
        self.failUnlessEqual(response.status_code, 200)
        self.failDiffUnlessEqual("../testdata/t0/selections.html", response.content, "/reports/")

        response = self.client.get('/selections/4/')
        self.failUnlessEqual(response.status_code, 200)
        self.failDiffUnlessEqual("../testdata/t0/selections-4.html", response.content, "/reports/1/")

        response = self.client.get('/results/')
        self.failUnlessEqual(response.status_code, 200)
        self.failDiffUnlessEqual("../testdata/t0/results0.html", response.content, "/results/")

        for contest_id in [4]:
            contest = models.Contest.objects.get(id=contest_id)
            contest.selected=True
            contest.save()

        for auditunit in [109]:
            au = models.ContestBatch.objects.get(id=auditunit)
            au.selected=True
            au.save()

        response = self.client.get('/results/')
        self.failUnlessEqual(response.status_code, 200)
        self.failDiffUnlessEqual("../testdata/t0/results.html", response.content, "/results/")

    def test_stats(self):
        "Try /stats/"

        response = self.client.get('/stats/')
        self.failUnlessEqual(response.status_code, 200)

class SimpleTestCsv(SimpleTest):
    "Separate from SimpleTest to allow each to be run as independent labels"

    def test_csv(self):
        "Try parsing csv data and comparing tally() output"

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

