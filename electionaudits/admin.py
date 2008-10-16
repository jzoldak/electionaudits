from django.contrib import admin
from electionaudits.models import *

class VoteCountAdmin(admin.ModelAdmin):
    "Modify default layout of admin form"
    list_display = ['votes', 'choice', 'contest_batch']

admin.site.register(CountyElection)
admin.site.register(Batch)
admin.site.register(Contest)
admin.site.register(ContestBatch)
admin.site.register(Choice)
admin.site.register(VoteCount, VoteCountAdmin)
