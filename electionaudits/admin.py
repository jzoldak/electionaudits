from django.contrib import admin
from electionaudits.models import *

class ContestInline(admin.TabularInline):
    model = Contest

class CountyElectionAdmin(admin.ModelAdmin):
    inlines = [ ContestInline, ]

class HandVoteCountInline(admin.TabularInline):
    model = HandVoteCount

class HandContestBatchAdmin(admin.ModelAdmin):
    inlines = [ HandVoteCountInline, ]

class VoteCountInline(admin.TabularInline):
    model = VoteCount

class ContestBatchAdmin(admin.ModelAdmin):
    inlines = [ VoteCountInline, ]

class VoteCountAdmin(admin.ModelAdmin):
    "Modify default layout of admin form"
    list_display = ['votes', 'choice', 'contest_batch']

class HandVoteCountAdmin(admin.ModelAdmin):
    "Modify default layout of admin form"
    list_display = ['votes', 'choice', 'contest_batch']

admin.site.register(CountyElection, CountyElectionAdmin)
admin.site.register(Batch)
admin.site.register(Contest)
admin.site.register(ContestBatch, ContestBatchAdmin)
admin.site.register(HandContestBatch, HandContestBatchAdmin)
admin.site.register(Choice)
admin.site.register(VoteCount, VoteCountAdmin)
admin.site.register(HandVoteCount, HandVoteCountAdmin)
admin.site.register(Margin)
