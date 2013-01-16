from django.conf.urls.defaults import patterns, url

from metasettings.views import dashboard

urlpatterns = patterns(
    '',
    url(r'^dashboard/(?:(?P<status>(language|currency)+)/)?$',
        dashboard,
        name='metasettings_dashboard'),
)
