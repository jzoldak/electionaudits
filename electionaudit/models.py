from django.db import models

from django.contrib import admin

class Batch(models.Model):
    "A batch of ballots all counted at the same time and stored together"

    name = models.CharField(max_length=200)
    type = models.CharField(max_length=20, help_text="Absentee, Early etc.")

    def __str__(self):
        return "%s" % (self.name)

class AuditUnit(models.Model):
    "A collection of Batches for a particular Contest which can be published for auditing"

    #id = models.CharField(max_length=200)

class Contest(models.Model):
    "The name of a race, and the associated margin, etc"

    name = models.CharField(max_length=200)

    # or provide external vote counts and calculate this?
    margin = models.FloatField()
    
    def __str__(self):
        return "%s" % (self.name)

class Choice(models.Model):
    "A candidate or issue name: an alternative in a Contest"

    choice = models.CharField(max_length=200)
    contest = models.ForeignKey(Contest)

    #slug = choice[0:6]

    def __str__(self):
        return "%s" % (self.choice)

class VoteCount(models.Model):
    "The count of votes for a particular Choice which are in the same Batch"

    votes = models.IntegerField()
    choice = models.ForeignKey(Choice)
    batch = models.ForeignKey(Batch)

    cumulative = models.BooleanField()

    def __str__(self):
        return "%s" % (self.votes)
        #return "%s:\t%d" % (choice.choice, self.votes)

"""
class Election(models.Model):

dubious: - use flag intstead
class CumVoteCount(VoteCount)
"""

admin.site.register(VoteCount)
admin.site.register(Choice)
admin.site.register(Contest)
admin.site.register(Batch)
admin.site.register(AuditUnit)
