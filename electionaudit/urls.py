from django.conf.urls.defaults import *

urlpatterns = patterns(r'',
    #(r'^$', 'electionaudit.views.index'),
)

"""
from electionaudit.models import *

info_dict = {
    'queryset': Entry.objects.all(),
    'date_field': 'pub_date',
}

urlpatterns = patterns('django.views.generic.date_based',
   (r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w]+)/$', 'object_detail', info_dict),
   (r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/$',               'archive_day',   info_dict),
   (r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/$',                                'archive_month', info_dict),
   (r'^(?P<year>\d{4})/$',                                                    'archive_year',  info_dict),
   (r'^$',                                                                    'archive_index', info_dict),
)

urlpatterns = patterns(w'',
    (r'^$', 'electionaudit.views.index'),
    (r'^(?P<poll_id>\d+)/$', 'electionaudit.views.detail'),
    (r'^(?P<poll_id>\d+)/results/$', 'electionaudit.views.results'),
    (r'^(?P<poll_id>\d+)/vote/$', 'electionaudit.views.vote'),
)
"""
