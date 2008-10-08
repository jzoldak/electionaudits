# Add "push" function to push into pipeline (static lists) of stuff to commit
#  maintain list for each (election, contest, type)
# add "save" function to save into database

class Pipe:
    """Accumulate some AuditUnits to be saved, until they are big enough
    to preserve privacy.
    This is a very simple implementation which keeps the AuditUnits in order.
    Others which work harder to maximize the number of AuditUnits can be
    written and plugged into the pushAuditUnit call.
    """

    def __init__(self):
        self.preserve = AuditUnit()
        self.building = AuditUnit()

    def __str__(self):
        return "preserve: %s\nbuilding: %s" % (self.preserve, self.building)

    def push(self, au, min_ballots):
        print "pushing", au

        if au.contest_ballots() + self.building.contest_ballots() >= min_ballots:
            self.preserve.save()
            self.preserve = self.building.combine(au)
            self.building = AuditUnit()
        else:
            self.building = self.building.combine(au)

    def flush(self):
        if self.building:
            if not self.preserve:
                raise RuntimeError("Not enough ballots for privacy")
            self.preserve = self.preserve.combine(self.building)

        self.preserve.save()

def pushAuditUnit(au, min_ballots=5, method=Pipe):
    """push an AuditUnit thru its appropriate pipeline, accumulating
    votes until publicising it won't violate privacy.

    >>> a1 = AuditUnit('e1', 'c1', 'AB', ['b1'], A=4, B=0)
    >>> pushAuditUnit(a1)
    >>> flushPipes()
    >>> a2 = AuditUnit('e1', 'c1', 'AB', ['b1'], A=1, B=0)

    """

    key = (au.election, au.contest, au.type)
    # create a new pipe (a Pipe, by default) if one isn't there now
    AuditUnit.pipeline[key] = AuditUnit.pipeline.get(key, method())
    AuditUnit.pipeline[key].push(au, min_ballots)

def flushPipes():
    """Flush out all the pipelines"""

    for pipe in AuditUnit.pipeline:
        pipe.flush()
    AuditUnit.pipeline = {}


class AuditUnit:
    """A collection of all the VoteCounts for a particular Contest
    in a set of Batches which can be published for auditing.  A combination
    of one or more ContestBatch classes, as a python data structure.
    batches is a list of batch names.
    votecounts is a dictionary of candidates and votes.
    """

    # A different pipe for each type of AuditUnit which shouldn't be mixed
    # The key is (au.election, au.contest, au.type)
    pipeline = {}

    def __init__(self, election=None, contest=None, type=None, batches=None, **votecounts):
        self.election = election
        self.contest = contest
        self.type = type
        self.batches = batches
        self.votecounts = votecounts

    def contest_ballots(self):
        return sum(votes for votes in self.votecounts.values())

    def save(self):
        if self.votecounts != {}:
            print "time to preserve %s" % self

    def __cmp__(self, other):
        return cmp(self.contest_ballots(), other.contest_ballots())

    def __str__(self):
        return "%s_%s_%s_%s_%s" % (self.election, self.contest, self.type, self.batches, self.votecounts)

    def __neg__(self):
        return AuditUnit(self.election, self.contest, self.type, self.batches, **dict((key, -val) for (key, val) in self.votecounts.iteritems()))

    def combine(self, other):
        if self.votecounts == {}:
            return other

        if self.election != other.election or self.contest != other.contest or self.type != other.type:
            raise ValueError("election, contest, and type must match")

        vcs = self.votecounts.copy()
        for (key, v2) in other.votecounts.items():
            vcs[key] = vcs.get(key, 0) + v2

        return AuditUnit(self.election, self.contest, self.type, self.batches + other.batches, **vcs )
