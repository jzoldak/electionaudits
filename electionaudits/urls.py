from django.conf.urls.defaults import *
from electionaudits.models import *
from django.contrib import databrowse
from django.conf import settings

databrowse.site.register(CountyElection)
databrowse.site.register(Batch)
databrowse.site.register(Tabulation)
databrowse.site.register(Contest)
databrowse.site.register(ContestBatch)
databrowse.site.register(HandContestBatch)
databrowse.site.register(Choice)
databrowse.site.register(VoteCount)
databrowse.site.register(HandVoteCount)
databrowse.site.register(Margin)

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

# electionaudits custom views

urlpatterns = patterns('electionaudits.views',
    (r'^eml510/\w*/ea510_style.xsl',    'eaxsl'),
    (r'^eml510/\w*/ea510rows.xsl',      'eaxslr'),
    (r'^eml510/(?P<contest>\w*)/$',     'eml510'),
    (r'^reports/(?P<contest>\w*)/$',    'report'),
    (r'^selections/(?P<contest>\w*)/$', 'report'),
    (r'^kmreports/(?P<contest>\w*)/$',    'kmreport'),
    (r'^kmresults/(?P<contest>\w*)/$', 'kmresult'),
    (r'^results/$',                     'results'),
    (r'^parse/$',     		        'parse'),
    (r'^stats/$',     		        'stats'),
)

urlpatterns += patterns('',
    (r'^databrowse/(.*)', databrowse.site.root),
)

urlpatterns += patterns('electionaudits',
    (r'^charts/simple.png$', 'charts.simple'),
)

# Generic views

urlpatterns += patterns('django.views.generic.simple',
    (r'^$',             'direct_to_template', {'template': 'electionaudits/index.html'}),
)

urlpatterns += patterns('django.views.generic.list_detail',
    (r'^reports/$',                     'object_list',     dict(contest_dict, template_name="electionaudits/reports.html")),
    (r'^kmreports/$',                   'object_list',     dict(contest_dict, template_name="electionaudits/kmreports.html")),
    (r'^selections/$',                  'object_list',     dict(contest_dict, template_name="electionaudits/reports.html")),
    (r'^contests/$',                    'object_list',     contest_dict),
    (r'^contests/(?P<object_id>\d+)/$', 'object_detail',   contest_dict),
    (r'^votecounts/$',                    'object_list',     votecount_dict),
    (r'^votecounts/(?P<object_id>\d+)/$', 'object_detail',   votecount_detail_dict),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^validator/', include('lukeplant_me_uk.django.validator.urls')))
