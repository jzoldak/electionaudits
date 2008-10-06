from django.conf.urls.defaults import *
from electionaudit.models import *
from django.contrib import databrowse
import audittools.settings

databrowse.site.register(CountyElection)
databrowse.site.register(AuditUnit)
databrowse.site.register(Batch)
databrowse.site.register(Contest)
databrowse.site.register(ContestBatch)
databrowse.site.register(Choice)
databrowse.site.register(VoteCount)

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

# electionaudit custom views

urlpatterns = patterns('electionaudit.views',
    #(r'^reports/(?P<contest>\w*)/$',            'report'),
)

urlpatterns += patterns('',
    (r'^databrowse/(.*)', databrowse.site.root),
)

# Generic views

urlpatterns += patterns('django.views.generic.simple',
    (r'^$',             'direct_to_template', {'template': 'electionaudit/index.html'}),
)

urlpatterns += patterns('django.views.generic.list_detail',
    (r'^reports/$',                     'object_list',     dict(contest_dict, template_name="electionaudit/reports.html")),
    (r'^reports/(?P<object_id>\d+)/$',  'object_detail',   dict(contest_dict, template_name="electionaudit/report.html")),
    (r'^contests/$',                    'object_list',     contest_dict),
    (r'^contests/(?P<object_id>\d+)/$', 'object_detail',   contest_dict),
    (r'^votecounts/$',                    'object_list',     votecount_dict),
    (r'^votecounts/(?P<object_id>\d+)/$', 'object_detail',   votecount_detail_dict),
)

if audittools.settings.DEBUG:
    urlpatterns += patterns('',
        (r'^validator/', include('lukeplant_me_uk.django.validator.urls')))

"""
urls to consider
/elections/
/election/contest stats
"""
