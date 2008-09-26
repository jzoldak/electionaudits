from django.db import models

class Election(models.Model):
    "An election, comprising a set of Contests and Batches of votes"

    name = models.CharField(max_length=200)

    def __unicode__(self):
        return "%s" % (self.name)

class Contest(models.Model):
    "The name of a race, and the associated margin of victory, etc"

    name = models.CharField(max_length=200)

    # or provide external vote counts and calculate this?
    margin = models.FloatField(default=0.01)
    
    def __unicode__(self):
        return "%s" % (self.name)

class AuditUnit(models.Model):
    """A collection of all the VoteCounts for a particular Contest
    in a set of Batches which can be published for auditing"""

    name = models.CharField(max_length=200)

    def __unicode__(self):
        return "%s" % (self.name)

class Batch(models.Model):
    "A batch of ballots all counted at the same time and stored together"

    name = models.CharField(max_length=200)
    election = models.ForeignKey(Election)
    type = models.CharField(max_length=20, help_text="Absentee, Early etc.")

    def __unicode__(self):
        return "%s/%s" % (self.name, self.type)

class Choice(models.Model):
    "A candidate or issue name: an alternative for a Contest"

    name = models.CharField(max_length=200)

    #slug = choice[0:6]

    def __unicode__(self):
        return "%s" % (self.name)

class VoteCount(models.Model):
    "The count of votes for a particular Choice which are in the same Batch and Contest"

    votes = models.IntegerField()
    choice = models.ForeignKey(Choice)
    batch = models.ForeignKey(Batch)
    contest = models.ForeignKey(Contest)

    cumulative = models.BooleanField()

    def __unicode__(self):
        return "%d\t%s\t%s\t%s" % (self.votes, self.choice.name, self.contest, self.batch.name)
