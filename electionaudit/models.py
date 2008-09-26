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
    margin = models.FloatField()
    
    def __unicode__(self):
        return "%s" % (self.name)

class AuditUnit(models.Model):
    "A collection of Batches for a particular Contest which can be published for auditing"

    name = models.CharField(max_length=200)

    def __unicode__(self):
        return "%s" % (self.name)

class Batch(models.Model):
    "A batch of ballots all counted at the same time and stored together"

    name = models.CharField(max_length=200)
    election = models.ForeignKey(Election)
    type = models.CharField(max_length=20, help_text="Absentee, Early etc.")

    audit_unit = models.ForeignKey(AuditUnit, default=None)

    def __unicode__(self):
        return "%s" % (self.name)

class Choice(models.Model):
    "A candidate or issue name: an alternative in a Contest"

    choice = models.CharField(max_length=200)
    contest = models.ForeignKey(Contest)

    #slug = choice[0:6]

    def __unicode__(self):
        return "%s" % (self.choice)

class VoteCount(models.Model):
    "The count of votes for a particular Choice which are in the same Batch"

    votes = models.IntegerField()
    choice = models.ForeignKey(Choice)
    batch = models.ForeignKey(Batch)

    cumulative = models.BooleanField()

    def __unicode__(self):
        return "%d\t%s\t%s" % (self.votes, self.choice.choice, self.batch.name)
