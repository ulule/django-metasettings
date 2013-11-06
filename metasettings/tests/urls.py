from django.conf.urls import patterns, url, include
from django.http import HttpResponse


def root(request):
    return HttpResponse('Ok')


urlpatterns = patterns(
    '',
    url(r'^$',
        root,
        name='root'),

    (r'^',
        include('metasettings.urls'))
)
