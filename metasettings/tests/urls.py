from django.conf.urls import url, include
from django.http import HttpResponse


def root(request):
    return HttpResponse('Ok')


urlpatterns = [
    url(r'^$',
        root,
        name='root'),

    url(r'^',
        include('metasettings.urls'))
]
