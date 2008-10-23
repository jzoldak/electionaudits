"""Generate a relationship diagram via django-extensions and
 ./manage.py graph_models electionaudits -g -o ../doc/model_graph.png
"""

import sys
import logging
import StringIO
from django.db import models
from django.core.cache import cache
from electionaudits import varsize

class CountyElection(models.Model):
    "An election, comprising a set of Contests and Batches of votes"

    name = models.CharField(max_length=200)

    def __unicode__(self):
        return "%s" % (self.name)

class Contest(models.Model):
    "The name of a race, and the associated margin of victory, etc"

    name = models.CharField(max_length=200)

    # or provide external vote counts and calculate this?
    margin = models.FloatField(blank=True, null=True,
                    help_text="(Winner - Second) / total, in percent" )

    def tally(self):
        "Tally up all the choices and calculate margins"

        total = 0
        winner = Choice(name="None", votes=0, contest=self)
        second = Choice(name="None", votes=0, contest=self)

        for choice in self.choice_set.all():
            choice.tally()
            total += choice.votes
            if choice.name not in ["Under", "Over"]:
                if choice.votes >= winner.votes:
                    second = winner
                    winner = choice
                elif choice.votes >= second.votes:
                    second = choice

        if winner.votes > 0:
            self.margin = (winner.votes - second.votes) * 100.0 / total
            self.save()
        else:
            self.margin = -1.0       # => float('nan') after windows fix in python 2.6 
            # don't save for now - may run in to odd NULL problems

        return {'contest': self.name,
                'total': total,
                'winner': winner.name,
                'winnervotes': winner.votes,
                'second': second.name,
                'secondvotes': second.votes,
                'margin': self.margin }

    def stats(self):
        "Generate selection statistics for this Contest."

        cbs = [(cb.contest_ballots(), str(cb.batch))
               for cb in self.contestbatch_set.all()]

        return selection_stats(cbs, self.margin/100.0, self.name)

    def __unicode__(self):
        return "%s" % (self.name)

class Batch(models.Model):
    "A batch of ballots all counted at the same time and stored together"

    name = models.CharField(max_length=200)
    election = models.ForeignKey(CountyElection)
    type = models.CharField(max_length=20, help_text="AB for Absentee, EV for Early, ED for Election")

    def __unicode__(self):
        return "%s:%s" % (self.name, self.type)

    class Meta:
        unique_together = ("name", "election", "type")

class ContestBatch(models.Model):
    "The set of VoteCounts for a given Contest and Batch"

    contest = models.ForeignKey(Contest)
    batch = models.ForeignKey(Batch)

    def contest_ballots(self):
        return sum(a.votes for a in self.votecount_set.all())

    def __unicode__(self):
        return "%s:%s" % (self.contest, self.batch)

    class Meta:
        unique_together = ("contest", "batch")

class Choice(models.Model):
    "A candidate or issue name: an alternative for a Contest"

    name = models.CharField(max_length=200)
    votes = models.IntegerField(null=True, blank=True)
    contest = models.ForeignKey(Contest)

    def tally(self):
        "Tally up all the votes for this choice and save result"

        from django.db import connection
        cursor = connection.cursor()
        cursor.execute('SELECT sum(votes) AS total_votes FROM electionaudits_votecount WHERE "choice_id" = %d' % self.id)

        row = cursor.fetchone()
        self.votes = row[0]
        self.save()
        return self.votes

    def __unicode__(self):
        return "%s" % (self.name)

class VoteCount(models.Model):
    "The count of votes for a particular Choice in a ContestBatch"

    votes = models.IntegerField()
    choice = models.ForeignKey(Choice)
    contest_batch = models.ForeignKey(ContestBatch)

    def __unicode__(self):
        return "%d\t%s\t%s\t%s" % (self.votes, self.choice.name, self.contest_batch.contest, self.contest_batch.batch)

    class Meta:
        unique_together = ("choice", "contest_batch")

def selection_stats(units, margin=0.01, name="test", alpha=0.08, s=0.20):
    """Prepare statistics on how many audit units should be selected
    in order to be able to reduce the risk of confirming an incorrect
    outcome to a given probability.
    units = a list of audit units, giving just size of each
    margin = margin of victory, between 0 and 1
    name = name for this contest
    alpha = significance level desired = 1 - confidence
    s = maximum within-precinct miscount as a fraction from 0.0 to 1.0

    Capture a dictionary of statistics and printed results.
    Cache the results for speed.
    """

    cachekey = "%s:%r:%f:%f" % (name, margin, alpha, s)
    saved = cache.get(cachekey)
    logging.debug("selection_stats: %d cached. contest %s" % (len(cache._expire_info), name))

    if saved:
        return saved

    if not margin:
        return {}

    save = sys.stdout
    sys.stdout = StringIO.StringIO()
    try:
        stats = varsize.paper(units, name, margin, alpha, s)
    except Exception, e:
        logging.exception("selection_stats: contest %s" % (name))
        return {}
    stats['prose'] = sys.stdout.getvalue()
    sys.stdout = save

    cache.set(cachekey, stats, 86400)
    return stats
