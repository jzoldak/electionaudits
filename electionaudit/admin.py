from django.contrib import admin
from electionaudit.models import *

class VoteCountAdmin(admin.ModelAdmin):
    list_display = ['votes', 'choice', 'contest_batch']

admin.site.register(CountyElection)
admin.site.register(AuditUnit)
admin.site.register(Batch)
admin.site.register(Contest)
admin.site.register(ContestBatch)
admin.site.register(Choice)
admin.site.register(VoteCount, VoteCountAdmin)
