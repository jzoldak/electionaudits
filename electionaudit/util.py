class AuditUnit:
    """A collection of all the VoteCounts for a particular Contest
    in a set of Batches which can be published for auditing.  A combination
    of one or more ContestBatch classes, as a python data structure."""

    
    def __init__(self, contest, batches, **votecounts):
        self.contest = contest
        self.batches = batches
        self.votecounts = votecounts

    #def __cmp__(self, other):

    def __unicode__(self):
        return "%s/%s/%s" % (self.contest, self.batches, self.votecounts)

    def __neg__(self):
        return AuditUnit(self.contest, self.batches, **dict((key, -val) for (key, val) in self.votecounts.iteritems()))
            
    def __add__(self, other):
        if self.contest != other.contest:
            raise TypeError

        vcs = self.votecounts.copy()
        for (key, v2) in other.votecounts.items():
            vcs[key] = vcs.get(key, 0) + v2
        
        return AuditUnit(self.contest, self.batches + other.batches, **vcs )
