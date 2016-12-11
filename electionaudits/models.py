"""Generate a relationship diagram via django-extensions and
 ./manage.py graph_models electionaudits -g -o ../doc/model_graph.png --settings settings_debug
"""

import sys
import math
import logging
import StringIO
import operator
import itertools
from django.db import models
from django.db import transaction
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

class Tabulation(models.Model):
    """A tabulation of some ballots.
    Can be either the primary machine tabulation,
    or a manual hand tabulation.
    """

    name = models.CharField(max_length=200)

class Contest(models.Model):
    "The name of a race, the associated margin of victory, and other parameters"

    name = models.CharField(max_length=200)
    election = models.ForeignKey(CountyElection)
    numWinners = models.IntegerField(default = 1,
                    help_text="Number of winners to be declared" )
    confidence = models.IntegerField(default = 75,
                    help_text="Desired level of confidence in percent, from 0 to 100, assuming WPM of 20%" )
    #confidence_eb = models.IntegerField(default = 50,
    #                help_text="Desired level of confidence in percent, from 0 to 100, incorporating rigorous error bounds" )
    proportion = models.FloatField(default = 100.0,
                    help_text="This county's proportion of the overall number of votes in this contest" )
    min_margin = models.FloatField(blank=True, null=True,
                    help_text="Minimum margin as a fraction of total contest ballots, calculated by tally()" )
    overall_margin = models.FloatField(blank=True, null=True,
                    help_text="(Winner - Second) / total including under and over votes, in percent" )
    U = models.FloatField(blank=True, null=True,
                    help_text="Total possible miscount / total apparent margin." )
    margin_offset = models.IntegerField(default = 0,
                    help_text="Adjust overall margins by this amount, e.g. use a negative number for ballots yet to be counted." )

    selected = models.NullBooleanField(null=True, blank=True,
                    help_text="Whether contest has been selected for audit" )

    def calculate_margins(self):
        "Calculate overall Margin between each pair of winners and losers"

        choices = self.choice_set.all()
        ranked = sorted([choice for choice in choices if choice.name not in ["Under", "Over"]], key=lambda o: o.votes, reverse=True)
        winners = ranked[:self.numWinners]
        losers = ranked[self.numWinners:]

        if len(winners) == 0 or winners[0].votes == 0:
            logging.warning("Contest %s has no votes" % self)
            return ([], [], [])

        # margins between winners and losers

        margins={}

        for winner in winners:
            margins[winner] = {}
            for loser in losers:
                margins[winner][loser] = max(0, winner.votes - loser.votes + self.margin_offset)

                # FIXME: Look for, deal with ties....

        return (winners, losers, margins)

    @transaction.commit_on_success
    def error_bounds(self):
        "Calculate and save overall margins, and error bound 'u' for each audit unit."

        (winners, losers, margins)  = self.calculate_margins()

        # Delete existing Margin database entries for this contest
        Margin.objects.filter(contest = self).delete()

        # Store margins in the database
        for winner in winners:
            for loser in losers:
                margin, created = Margin.objects.get_or_create(votes = margins[winner][loser], winner = winner, loser = loser, contest = self)
                margin.save()

        self.U = 0.0

        # FIXME: probably faster to query the votecounts, sort by cb, and process them that way - fewer queries
        for au in self.contestbatch_set.all():
            au.u = 0.0
            vc = {}
            for voteCount in au.votecount_set.all():
                vc[voteCount.choice] = voteCount.votes

            for winner in winners:
                for loser in losers:
                    if margins[winner][loser] <= 0:
                        logging.warning("Margin in %s is %d for %s vs %s" % (self, margins[winner][loser], winner, loser))
                        continue
                    au.u = max(au.u, float(au.contest_ballots() + vc[winner] - vc[loser]) / margins[winner][loser])

            au.save()
            self.U = self.U + au.u

        self.save()

        return {'U': self.U,
                'winners': winners,
                'losers': losers,
                'margins': margins,
                }


    def tally(self):
        "Tally up all the choices and calculate margins"

        # First just calculate the winner and second place

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
            self.min_margin = (winner.votes - second.votes) * 100.0 / total
            self.save()
        else:
            self.min_margin = -1.0       # => float('nan') after windows fix in python 2.6 
            # don't save for now - may run in to odd NULL problems

        return {'contest': self.name,
                'total': total,
                'winner': winner.name,
                'winnervotes': winner.votes,
                'second': second.name,
                'secondvotes': second.votes,
                'margin': self.min_margin }

    def stats(self, confidence=None, s=0.20):
        """Generate selection statistics for this Contest.
        Use given confidence (percentage). The default of None means
        to use the confidence in the database for this contest.
        The "s" parameter gives the maximum Within Precinct Miscount to assume, which
        defaults to the fraction 0.20.
        """

        if not confidence:
            confidence = self.confidence

        cbs = [(cb.contest_ballots(), str(cb.batch))
               for cb in self.contestbatch_set.all()]

        m = self.overall_margin  or  self.min_margin
        # Test stats with lots of audit units: Uncomment to use
        #  (Better to turn this on and off via a GET parameter....)
        # cbs = [(500,)]*300 + [(200,)]*200 + [(40,)]*100
        return selection_stats(cbs, m/100.0, self.name, alpha=((100-confidence)/100.0), s=s, proportion=self.proportion)

    def threshhold(self):
        if (self.overall_margin  or  self.min_margin):
            return 1.0 / (self.overall_margin  or  self.min_margin)
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

    def km_result(self, n=None, factor=2.0, prng=None):
        """Return a list of selected contest_batches for the contest, based on
        error bounds and seed, and annotated with related hand counts and Kaplan-Markov factors.
        Return "n" selections, or "factor" times as many as the current
        confidence level requires.  "factor" defaults to 2.0 in order to show
        which contest batches may need to be audited if there are discrepancies.
        prng (Pseudo-Random Number Generator) is a function.  It defaults to Rivest's
        Sum of Square Roots, but can be specified as a function that returns numbers in the range [0, 1)

        FIXME: when contestbatch is selected multiple times, combine them and figure net_km
        Otherwise when there are multiples, in the view, the cum_km calculated during the last time it
        was selected shows up for the previous selections also, in a confusing way.

        """

        if not self.election.random_seed:
            return

        contest_batches = self.contestbatch_set.all().select_related()
        weights = [cb.u for cb in contest_batches]

        confidence = self.confidence
        if confidence == 90:	# FIXME: make this more general - use log ratio like this?
            confidence = 50

        alpha = ((100-confidence)/100.0)
        if n == None:
            n = int(math.ceil(math.log(alpha) / math.log(1.0 - (1.0 / self.U))) * factor)	#  FIXME: deal with U = None

        #  These values are for testing against the Kaplan-Markov example by Lindeman which uses R's implementation of the Mersenne Twister (which uses a different seed initialization than Python's implementation) for a seed of 20100110.

        # Demonstrate significant discrepancies: insert .723503681 at position 7 with discrepancy of 60,
        #  and later small unit 0.24212419885498093 with discrepancy of 4
        # starting after the original 47th number (0.90055056) recycle the initial 7 numbers to provide some
        # units with existing low discrepancy rates to make up for the big discrepancies
        # n = 53

        prng = itertools.cycle([
                0.40827853, 0.80061871, 0.94676299, 0.49736872, 0.46192904, 0.81279404,
                0.723503681,     0.83129304, 0.16215752, 0.98246675, 0.95694084, 0.67667001, 0.60017428, 0.36931386,
                0.24212419885498093,   0.80239029, 0.77339991, 0.03171216, 0.27891897, 0.68962453, 0.36474152, 0.68695872, 0.98093805, 0.30901657, 0.97122549, 0.76789247, 0.56631869, 0.31349720, 0.03224969, 0.49095661, 0.12090347, 0.09948674, 0.62830930, 0.10122452, 0.28973657, 0.99603961, 0.54367589, 0.12708358, 0.12108279, 0.03328502, 0.56681770, 0.82867559, 0.34289365, 0.58856273, 0.11031500, 0.27732952, 0.04791692, 0.19352317, 0.90055056,
                0.619219230, 0.422998193, 0.176488403, 0.098456706, 
                0.945349626, 0.005172588, 0.231380854, 0.322367015,
                0.40827853, 0.80061871, 0.94676299, 0.49736872, 0.46192904, 0.81279404, 0.83129304,
                0.723503681, 0.628840660, 0.945349626, 0.005172588, 0.231380854, 0.322367015, 0.619219230, 0.422998193, 0.176488403, 0.098456706, 0.287239747, 0.304059427, 0.799412787, 0.858068369, 0.052733564, 0.148171730, 0.597793150, 0.257195494, 0.015788411, 0.857327704, 0.375756592, 0.794498659, 0.836206789, 0.915773934, 0.854490657, 0.604662348, 0.213979315, 0.791392480, 0.106467584, 0.858819452, 0.363092949, 0.294402013, 0.823552060, 0.614129400, 0.112239813, 0.904572994, 0.183575009, 0.134886135, 0.789411610, 0.790145970, 0.127183767, 0.103685433, 0.747877328, 0.791619243, 0.186384418, 0.842586009, 0.902961352 ]).next

        # Uncomment these to replicate kaplan-example exactly
        # n = 47
        # prng = itertools.cycle([ 0.40827853, 0.80061871, 0.94676299, 0.49736872, 0.46192904, 0.81279404, 0.83129304, 0.16215752, 0.98246675, 0.95694084, 0.67667001, 0.60017428, 0.36931386, 0.80239029, 0.77339991, 0.03171216, 0.27891897, 0.68962453, 0.36474152, 0.68695872, 0.98093805, 0.30901657, 0.97122549, 0.76789247, 0.56631869, 0.31349720, 0.03224969, 0.49095661, 0.12090347, 0.09948674, 0.62830930, 0.10122452, 0.28973657, 0.99603961, 0.54367589, 0.12708358, 0.12108279, 0.03328502, 0.56681770, 0.82867559, 0.34289365, 0.58856273, 0.11031500, 0.27732952, 0.04791692, 0.19352317, 0.90055056 ]).next

        if not prng:
            # The default pseudo-random number generator is to call ssr (Rivest's Sum of Square Roots algorithm)
            # with an incrementing first argument, and the current election seed: ssr(1, seed); ssr(2, seed), etc.
            prng = itertools.imap(erandom.ssr, itertools.count(1), itertools.repeat(self.election.random_seed)).next

        # FIXME: avoid tricks to retain random values here and make this and weightedsample() into
        # some sort of generator that returns items that are nicely bundled with associated random values
        random_values = [prng() for i in range(n)]
        prng_replay = iter(random_values).next

        sample = erandom.weightedsample(contest_batches, weights, n, replace=True, prng=prng_replay)
        # Add handcount votecounts, if any, and statistical fields to each contestbatch in the sample
        cum_km = 1.0
        cum_kms = []
        for contestbatch in sample:
            contestbatch.handcountcbs()
            if contestbatch.handcounts:
                contestbatch.net_km = contestbatch.km   # FIXME for multiple uses of this contestbatch
                cum_km *= contestbatch.net_km
                cum_kms.append(cum_km)
            else:
                cum_kms.append(None)

        return zip(sample, random_values, cum_kms)

    def select_units(self, stats):
        """Return a list of contest_batches for the contest,
        augmented with ssr, threshhold and priority, 
        in selection priority order if possible"""

        contest_batches = self.contestbatch_set.all()

        wpm = 0.2

        audit_units = []
        for cb in contest_batches:
            cb.stats = stats
            cb.margin = self.overall_margin  or  self.min_margin
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

    @transaction.commit_on_success
    def merge(self, other):
        "merge this Batch with another Batch, along with associated ContestBatches and VoteCounts"

        if self.election != other.election:
            logging.error("Error: %s is election %d but %s is election %d" % (self, self.election, other, other.election))

        if self.type != other.type:
            logging.error("Error: %s is type %d but %s is type %d" % (self, self.type, other, other.type))

        for other_cb in other.contestbatch_set.all():
            my_cb, created = ContestBatch.objects.get_or_create(contest = other_cb.contest, batch = self)
            my_cb.merge(other_cb)

        self.name += "+" + other.name
        self.ballots += other.ballots
        self.notes = (self.notes or "") + "; " + (other.notes or "")

        self.save()
        other.delete()

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
    u = models.FloatField(blank=True, null=True,
                    help_text="Maximum miscount / total apparent margin." )
    selected = models.NullBooleanField(null=True, blank=True,
                    help_text="Whether audit unit has been specifically targeted for audit" )
    notes = models.CharField(max_length=200, null=True, blank=True,
                    help_text="Free-form notes" )

    def threshhold(self):
        wpm = 0.2
        return 1.0 - math.exp(-(self.contest_ballots() * 2.0 * wpm) / self.contest.stats()['negexp_w'])

    def contest_ballots(self):
        "Sum of recorded votes and under/over votes.  C.v. batch.ballots"
        return sum(a.votes for a in self.votecount_set.all())

    def handcountcbs(self):
        """Add fields to this contestbatch including hand counts for
        the same contest and batch, if available,
        along with taints and and associated information
        """

        handcountcbs = HandContestBatch.objects.filter(contest = self.contest, batch = self.batch).order_by('-id')
        if handcountcbs:
            handcountcb = handcountcbs[0]
            self.votecounts = self.votecount_set.all()
            self.handcounts = handcountcb.handvotecount_set.all()

            (winners, losers, margins)  = self.contest.calculate_margins()  # FIXME: do this once for contest

            # FIXME: deal with zero margin
            # FIXME: deal with missing ones, mismatches

            vc = {}
            for votecount in self.votecount_set.all():
                vc[votecount.choice] = votecount.votes

            hc = {}
            for handcount in self.handcounts:
                hc[handcount.choice] = handcount.votes

            logging.debug("%s %s" % (winners, losers))

            # minimum error is the minumu float value to start with.  Yes, a bit extreme, but....
            self.e = -sys.float_info[0]
            for winner in winners:
                for loser in losers:
                    logging.debug("%f %s %s %d" % (self.e, winner, loser, margins[winner][loser]))
                    # FIXME: make sure zero margin is dealt with here or elsewhere
                    if margins[winner][loser] > 0:
                        try:
                            discrepancy = (vc[winner] - vc[loser]) - (hc[winner] - hc[loser])
                        except KeyError:
                            # FIXME.  For now, assume missing votecounts are zero
                            continue
                        e = float(discrepancy) / margins[winner][loser]
                        logging.debug("%d %f" % (discrepancy, e))
                        if e > self.e: 
                            self.e = e
                            self.discrepancy = discrepancy
                            self.taint_winner = winner
                            self.taint_loser = loser

            # FIXME: do we need to worry about these values being retained on the objects and seen when they aren't up-to-date?
            self.taint = self.e / self.u
            assert self.taint <= 1  # Should be impossible: e.g. negative vote counts.  Causes km value to be negative
            self.km = (1.0 - (1.0 / self.contest.U)) / (1.0 - self.taint)

        else:
            self.handcounts = ()

    @transaction.commit_on_success
    def merge(self, other):
        "merge this ContestBatch with another ContestBatch, along with associated VoteCounts"

        logging.debug("merging: %s and %s" % (self, other))

        for other_vc in other.votecount_set.all():
            my_vc, created = VoteCount.objects.get_or_create(contest_batch = self, choice = other_vc.choice, defaults={'votes': 0})
            logging.debug("merging: %s and %s" % (my_vc, other_vc))
            my_vc.votes += other_vc.votes
            my_vc.save()
            other_vc.delete()

        self.notes = (self.notes or "") + "; " + (other.notes or "") + "; M: " + str(self)
        self.save()
        other.delete()

    def taintfactor(self, discrepancy):
        """
        Return taint and Kaplan-Markov factor for a given discrepancy.
        Taint is equation 15 from Stark's "P-values" paper (2009).  
        FIXME: Assumes it is for the closest margin....
        """

        # First figure out the minumum margin out of all the winner-loser pairs for this contest
        min_margin = sys.maxint
        for choice in self.contest.choice_set.all():
            min_margin = min([min_margin] + [margin.votes for margin in Margin.objects.filter(winner = choice.id)])

        taint = (discrepancy * 1.0 / min_margin) / self.u
        # FIXME: warn if taint is > 1?  Should be impossible, causes return value to be negative
        return {'taint': taint, 'km': (1.0 - (1.0 / self.contest.U)) / (1.0 - taint)}

    def votes(self):
        "Return an array of the votes and choices for this ContestBatch, sorted in reverse order"

        return sorted([(vc.votes, vc.choice.name) for vc in self.votecount_set.all()], reverse=True)

    def __unicode__(self):
        return "%s:%s" % (self.contest, self.batch)

    class Meta:
        unique_together = ("contest", "batch")

class HandContestBatch(models.Model):
    "A Hand-count-audited ContestBatch"

    contest = models.ForeignKey(Contest)
    batch = models.ForeignKey(Batch)

    @staticmethod
    @transaction.commit_on_success
    def create(contestbatch):
        """For testing convenience, make up a hand count result (HandContestBatch
        and associated HandVoteCounts) that matches the machine counts of the given contestbatch"""

        handcontestbatch, created = HandContestBatch.objects.get_or_create(contest=contestbatch.contest, batch=contestbatch.batch)
        if not created:
            logging.error("HandContestBatch %s already exists" % (handcontestbatch))
            return handcontestbatch

        for votecount in contestbatch.votecount_set.all():
            HandVoteCount.objects.create(choice=votecount.choice, votes=votecount.votes, contest_batch=handcontestbatch)

        return handcontestbatch

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

class HandVoteCount(models.Model):
    "The count of votes for a particular Choice in a HandContestBatch"

    votes = models.IntegerField()
    choice = models.ForeignKey(Choice)
    contest_batch = models.ForeignKey(HandContestBatch)

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
    proportion = This county's proportion of the overall number of votes in this contest

    Capture a dictionary of statistics and printed results.
    Cache the results for speed.
    """

    cachekey = "%s:%r:%f:%f:%f" % (name, margin, alpha, s, proportion)
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

class Margin(models.Model):
    "Margin in votes between two Choices for a given tabulation"

    votes = models.IntegerField()
    winner = models.ForeignKey(Choice, related_name = 'winner')
    loser = models.ForeignKey(Choice, related_name = 'loser')
    contest = models.ForeignKey(Contest)

    def __unicode__(self):
        return "%s-%s" % (self.winner.name, self.loser.name)

    class Meta:
        unique_together = ("winner", "loser", "contest")
