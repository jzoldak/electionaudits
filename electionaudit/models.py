"""Generate a relationship diagram via django-extensions and
 ./manage.py graph_models electionaudit -g -o ../doc/model_graph.png
"""

from django.db import models

class CountyElection(models.Model):
    "An election, comprising a set of Contests and Batches of votes"

    name = models.CharField(max_length=200)

    def __unicode__(self):
        return "%s" % (self.name)

class Contest(models.Model):
    "The name of a race, and the associated margin of victory, etc"

    name = models.CharField(max_length=200)

    # or provide external vote counts and calculate this?
    margin = models.FloatField(null=True, blank=True, help_text="(Winner - Second) / total, in percent")

    def tally(self):
        "Tally up all the choices and calculate margins"

        total = 0
        winner = None
        second = None

        for choice in self.choice_set.all():
            choice.tally()
            total += choice.votes
            if choice.name not in ["Under", "Over"]:
                if not winner or choice.votes > winner.votes:
                    second = winner
                    winner = choice
                elif not second or choice.votes > second.votes:
                    second = choice

        if second and winner.votes > 0:
            self.margin = (winner.votes - second.votes) * 100.0 / total
            self.save()
        return self.margin

    def __unicode__(self):
        return "%s" % (self.name)

class Batch(models.Model):
    "A batch of ballots all counted at the same time and stored together"

    name = models.CharField(max_length=200)
    election = models.ForeignKey(CountyElection)
    type = models.CharField(max_length=20, help_text="AB for Absentee, EV for Early, EL for Election")

    def __unicode__(self):
        return "%s:%s" % (self.name, self.type)

class ContestBatch(models.Model):
    "The set of VoteCounts for a given Contest and Batch"

    contest = models.ForeignKey(Contest)
    batch = models.ForeignKey(Batch)

    def contest_ballots(self):
        return sum(a.votes for a in self.votecount_set.all())

    def __unicode__(self):
        return "%s:%s" % (self.contest, self.batch)

class Choice(models.Model):
    "A candidate or issue name: an alternative for a Contest"

    name = models.CharField(max_length=200)
    votes = models.IntegerField(null=True, blank=True)
    contest = models.ForeignKey(Contest)

    def tally(self):
        "Tally up all the votes for this choice and save result"

        from django.db import connection
        cursor = connection.cursor()
        cursor.execute('SELECT sum(votes) AS total_votes FROM electionaudit_votecount WHERE "choice_id" = %d' % self.id)

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
