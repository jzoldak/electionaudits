from django.conf.urls.defaults import *
from electionaudit.models import *
import settings

# electionaudit custom views

urlpatterns = patterns('electionaudit.views',
    #(r'^$',                                    'index'),
    (r'^reports/(?P<contest>\w*)/$',            'report'),
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
    (r'^contests/$',                    'object_list',     contest_dict),
    (r'^contests/(?P<object_id>\d+)/$', 'object_detail',   contest_dict),
    (r'^votecounts/$',                    'object_list',     votecount_dict),
    (r'^votecounts/(?P<object_id>\d+)/$', 'object_detail',   votecount_detail_dict),
)

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
