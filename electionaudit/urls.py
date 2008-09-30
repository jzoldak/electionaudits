from django.conf.urls.defaults import *
from electionaudit.models import *
import settings

# electionaudit custom views

urlpatterns = patterns('electionaudit.views',
    #(r'^reports/(?P<contest>\w*)/$',            'report'),
)

# Generic views

contest_dict = {
    'queryset': Contest.objects.all(),
}

votecount_dict = {
    'queryset': VoteCount.objects.all(),
    'template_object_name' : 'votecounts',
}

votecount_detail_dict = {
    'queryset': VoteCount.objects.all(),
    'template_object_name' : 'votecount',
}

urlpatterns += patterns('django.views.generic.list_detail',
    (r'^reports/$',                     'object_list',     dict(contest_dict, template_name="electionaudit/reports.html")),
    (r'^reports/(?P<object_id>\d+)/$',  'object_detail',   dict(contest_dict, template_name="electionaudit/report.html")),
    (r'^contests/$',                    'object_list',     contest_dict),
    (r'^contests/(?P<object_id>\d+)/$', 'object_detail',   contest_dict),
    (r'^votecounts/$',                    'object_list',     votecount_dict),
    (r'^votecounts/(?P<object_id>\d+)/$', 'object_detail',   votecount_detail_dict),
)

from django.contrib import databrowse
urlpatterns += patterns('',
    (r'^databrowse/(.*)', databrowse.site.root),
)

from django.contrib import databrowse

databrowse.site.register(CountyElection)
databrowse.site.register(AuditUnit)
databrowse.site.register(Batch)
databrowse.site.register(Contest)
databrowse.site.register(ContestBatch)
databrowse.site.register(Choice)
databrowse.site.register(VoteCount)

if settings.DEBUG:
    urlpatterns = urlpatterns + patterns('',
        (r'^validator/', include('lukeplant_me_uk.django.validator.urls')))

"""
urls to consider

/index
/reports/
/reports/<contest>
/elections/
votecount/<batch>
/contest/report/ auditable report
/election/ list of batches
? list of contests
/election/contest stats
"""
