"""Generate a relationship diagram via django-extensions and
 ./manage.py graph_models electionaudits -g -o ../doc/model_graph.png --settings settings_debug
"""

import sys
import math
import logging
import StringIO
import operator
from django.db import models
from django.core.cache import cache
from electionaudits import varsize
import electionaudits.erandom as erandom

class CountyElection(models.Model):
    "An election, comprising a set of Contests and Batches of votes"

    name = models.CharField(max_length=200)
    random_seed = models.CharField(max_length=50, blank=True, null=True,
       help_text="The seed for random selections, from verifiably random sources.  E.g. 15 digits" )

    def __unicode__(self):
        return "%s" % (self.name)

class Contest(models.Model):
    "The name of a race, and the associated margin of victory, etc"

    name = models.CharField(max_length=200)
    election = models.ForeignKey(CountyElection)
    confidence = models.IntegerField(default = 75,
                    help_text="Desired level of confidence in percent, from 0 to 100" )
    proportion = models.FloatField(default = 100.0,
                    help_text="This county's proportion of the overall number of votes in this contest" )
    margin = models.FloatField(blank=True, null=True,
                    help_text="Calculated when data is parsed" )
    overall_margin = models.FloatField(blank=True, null=True,
                    help_text="(Winner - Second) / total including under and over votes, in percent" )

    #selected = models.NullBooleanField(null=True, blank=True,
    #                help_text="Whether contest has been selected for audit" )

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

    def stats(self, s=0.20):
        "Generate selection statistics for this Contest."

        cbs = [(cb.contest_ballots(), str(cb.batch))
               for cb in self.contestbatch_set.all()]

        m = self.overall_margin  or  self.margin
        # Test stats with lots of audit units: Uncomment to use
        #  (Better to turn this on and off via a GET parameter....)
        # cbs = [(500,)]*300 + [(200,)]*200 + [(40,)]*100
        return selection_stats(cbs, m/100.0, self.name, alpha=((100-self.confidence)/100.0), s=s, proportion=self.proportion)

    def threshhold(self):
        if (self.overall_margin  or  self.margin):
            return 1.0 / (self.overall_margin  or  self.margin)
        else:
            return ""

    def ssr(self):
        """Sum of Square Roots (SSR) pseudorandom number calculated from
        our id and the random seed for the election"""

        return erandom.ssr(self.id, self.election.random_seed)

    def priority(self):
        if self.ssr() == ""  or  self.threshhold() == "":
            return ""
        else:
            return self.threshhold() / self.ssr()

    def select_units(self, stats):
        """Return a list of contest_batches for the contest,
        augmented with ssr, threshhold and priority, 
        in selection priority order if possible"""

        contest_batches = self.contestbatch_set.all()

        wpm = 0.2

        audit_units = []
        for cb in contest_batches:
            cb.stats = stats
            cb.margin = self.overall_margin  or  self.margin
            cb.ssr = cb.batch.ssr()
            cb.threshhold = 1.0 - math.exp(-(cb.contest_ballots() * 2.0 * wpm) / stats['negexp_w'])
            if cb.ssr != "":
                cb.priority = cb.threshhold / cb.ssr
            else:
                cb.priority = ""
            audit_units.append(cb)

            if audit_units[0].priority != "":
                audit_units.sort(reverse=True, key=operator.attrgetter('priority'))

        return audit_units

    def __unicode__(self):
        return "%s" % (self.name)

class Batch(models.Model):
    "A batch of ballots all counted at the same time and stored together"

    name = models.CharField(max_length=200)
    election = models.ForeignKey(CountyElection)
    type = models.CharField(max_length=20, help_text="AB for Absentee, EV for Early, ED for Election")
    ballots = models.IntegerField(null=True, blank=True,
                    help_text="Number of ballots in the batch" )
    random = models.FloatField(null=True, blank=True,
                    help_text="Random number assigned for selection" )
    notes = models.CharField(max_length=200, null=True, blank=True,
                    help_text="Free-form notes" )

    def ssr(self):
        """Sum of Square Roots (SSR) pseudorandom number calculated from
        batch id and the random seed for the election"""

        return erandom.ssr(self.id, self.election.random_seed)

    def __unicode__(self):
        return "%s:%s" % (self.name, self.type)

    class Meta:
        unique_together = ("name", "election", "type")

class ContestBatch(models.Model):
    "The set of VoteCounts for a given Contest and Batch"

    contest = models.ForeignKey(Contest)
    batch = models.ForeignKey(Batch)
    selected = models.NullBooleanField(null=True, blank=True,
                    help_text="Whether audit unit has been selected for audit" )
    notes = models.CharField(max_length=200, null=True, blank=True,
                    help_text="Free-form notes" )

    def threshhold(self):
        wpm = 0.2
        return 1.0 - math.exp(-(self.contest_ballots() * 2.0 * wpm) / self.contest.stats()['negexp_w'])

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

def selection_stats(units, margin=0.01, name="test", alpha=0.08, s=0.20, proportion=100.0):
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

    for stat in ['ppebwr_work', 'ppebwr_precincts',
                 'negexp_work', 'negexp_precincts', 
                 'safe_work', 'safe_precincts', ]:
        stats[stat] = stats[stat] * proportion/100.0

    cache.set(cachekey, stats, 86400)
    return stats
