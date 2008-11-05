"""
AuditUnit class and logic to combine AuditUnits for anonymity.
"""

import logging
import electionaudits.models as models

class Pipe:
    """Accumulate some AuditUnits to be saved, until they are big enough
    to preserve privacy.
    This is a very simple implementation which keeps the AuditUnits in order.
    Others which work harder to maximize the number of AuditUnits can be
    written and plugged into the pushAuditUnit call.
    """

    def __init__(self):
        """self.building: build up enough ballots to save privately
        self.preserve: hold on to one unit prior to saving it in case we need
        to combine another undersized one with it.
        """

        self.preserve = AuditUnit()
        self.building = AuditUnit()

    def __str__(self):
        return "preserve: %s\nbuilding: %s" % (self.preserve, self.building)

    def push(self, au, min_ballots):
        "push the audit unit into the queue, and save any full units no longer needed"

        logging.debug("pushing %s" % au)

        if au.contest_ballots() + self.building.contest_ballots() >= min_ballots:
            self.preserve.save()
            self.preserve = self.building.combine(au)
            self.building = AuditUnit()
        else:
            self.building = self.building.combine(au)

    def flush(self):
        "flush the rest out"
        if self.building:
            if not self.preserve:
                logging.error("Not enough ballots for privacy" % self)
            self.preserve = self.preserve.combine(self.building)

        self.preserve.save()

def pushAuditUnit(au, min_ballots=25, method=Pipe):
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

    for pipe in AuditUnit.pipeline.values():
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

    def __init__(self, election=None, contest=None, type=None, batches=[], **votecounts):
        self.election = election
        self.contest = contest
        self.type = type
        self.batches = batches		# a list of batch names
        self.votecounts = votecounts

        if election and contest:
            election, created = models.CountyElection.objects.get_or_create(name=self.election)
            contest, created = models.Contest.objects.get_or_create(name=self.contest)

    def update(self, choice, votes):
        "Add votes to the audit unit.  Should really be a dict update?"

        if choice in self.votecounts:
            raise ValueError("There are already votes for %s in %s" % (choice, self))
        self.votecounts[choice] = int(votes)

    def contest_ballots(self):
        "Return total number of ballots for this contest, including over, under"

        return sum(votes for votes in self.votecounts.values())

    def save(self):
        "Save the AuditUnit to the database"

        if self.votecounts == {}:
            return

        logging.debug("saving %s" % self)

        election, created = models.CountyElection.objects.get_or_create(name=self.election)
        batch, created = models.Batch.objects.get_or_create(name=' '.join(self.batches), election=election, type=self.type )
        contest, created = models.Contest.objects.get_or_create(name=self.contest)

        # After contest etc is registered, we bail if no actual vote counts
        if self.contest_ballots() == 0:
            logging.debug("Zero batch: %s" % self)
            return

        contest_batch, created = models.ContestBatch.objects.get_or_create(contest=contest, batch=batch)
        for (choice, votes) in self.votecounts.items():
            choice, created = models.Choice.objects.get_or_create(name=choice, contest=contest)
            models.VoteCount.objects.create(choice=choice, votes=votes, contest_batch=contest_batch)

    def __cmp__(self, other):
        "Numerically compare number of contest_ballots in AuditUnit"
        return cmp(self.contest_ballots(), other.contest_ballots())

    def __str__(self):
        return "%s_%s_%s_%s_%d" % (self.election, self.contest, self.type, self.batches, self.contest_ballots())

    def __neg__(self):
        "Negate the AuditUnit, for subtraction"

        return AuditUnit(self.election, self.contest, self.type, self.batches, **dict((key, -val) for (key, val) in self.votecounts.iteritems()))

    def combine(self, other, subtract=False):
        """Combine two audit units into a new one.  If subtract is set,
        subtract "other" and only show batches from self.
        """

        if self.votecounts == {}:
            return other

        if other.votecounts == {}:
            return self

        if self.contest_ballots() == 0:
            logging.debug("Zero batch: %s" % other)
            return other

        if other.contest_ballots() == 0:
            if not subtract:	# if subtract, don't care about previous total
                logging.debug("Zero batch: %s" % self)
            return self

        if subtract:
            other = -other

        logging.debug("combining batches %s_%s (%d) and %s_%s (%d)\n%s\n%s" % (self.batches, self.type, self.contest_ballots(), other.batches, other.type, other.contest_ballots(), self, other))
        if self.election != other.election or self.contest != other.contest or self.type != other.type:
            raise ValueError("election, contest, and type must match:\n%s vs\n%s" % (self, other) )

        vcs = self.votecounts.copy()
        for (key, v2) in other.votecounts.items():
            if v2 < 0 and not subtract:
                raise ValueError("Negative vote count in %s: %s is %d" % (other, key, v2))
            vcs[key] = vcs.get(key, 0) + v2

        if subtract:
            newbatches = self.batches	# don't care about previous
        else:
            newbatches = self.batches + other.batches
            
        return AuditUnit(self.election, self.contest, self.type, newbatches, **vcs )
