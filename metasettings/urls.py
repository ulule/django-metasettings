from django.conf.urls import url

from .views import dashboard


urlpatterns = [
    url(r'^dashboard/(?:(?P<status>(language|currency)+)/)?$',
        dashboard,
        name='metasettings_dashboard'),
]
