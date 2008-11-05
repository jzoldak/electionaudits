import os
from django.test import TestCase
from electionaudits.management.commands.parse import Command
import electionaudits.parsers

class SimpleTest(TestCase):
    def failDiffUnlessEqual(self, string1, string2, testname):
        "Like failUnlessEqual, but shows diffs in context labeled with testname"

        if string1 != string2:
            import tempfile
            (savenew, name) = tempfile.mkstemp(suffix=".html")
            os.write(savenew, string2)
            os.close(savenew)
            print "New %s output saved in %s" % (testname, name)

            import difflib
            s1=string1.split('\n')
            s2=string2.split('\n')
            self.failUnlessEqual(string1, string2,
                                 testname + " content differs:\n" +
                                 '\n'.join(difflib.unified_diff(s1, s2) ))

    def test_reports(self):
        "Try /reports/ and /reports/1/ before and after reading testdata/t0"

        response = self.client.get('/reports/')
        self.failUnlessEqual(response.status_code, 200)
        
        c = Command()
        options = electionaudits.parsers.set_options(["-c", "-s"])
        c.handle("../testdata/t0", **options.__dict__)

        response = self.client.get('/reports/')
        self.failUnlessEqual(response.status_code, 200)
        prev_content = open("../testdata/t0/reports.html").read()
        self.failDiffUnlessEqual(prev_content, response.content, "/reports/")

        response = self.client.get('/reports/1/')
        self.failUnlessEqual(response.status_code, 200)

        """
        comment out until the sort order is always the same.

        prev_content = open("../testdata/t0/report.html").read()
        if response.content != prev_content:
            import difflib
            s1=prev_content.split('\n')
            s2=response.content.split('\n')
            self.failUnlessEqual(response.content, prev_content,
                                 "/reports/1 output differs:\n" +
                                 '\n'.join(difflib.unified_diff(s1, s2) ))
        """

    def test_stats(self):
        "Try /stats/"

        response = self.client.get('/stats/')
        self.failUnlessEqual(response.status_code, 200)
