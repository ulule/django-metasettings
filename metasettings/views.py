from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.views.generic.base import View

from . import signals
from .util import set_cookie, chunks
from .settings import CURRENCY_COOKIE_NAME, CURRENCY_LABELS, CURRENCY_CHOICES


class MetasettingsDashboard(View):
    http_method_names = ('post',)
    template_name = 'metasettings/dashboard.html'

    parameters = {
        'currency_code': {
            'choices': dict(CURRENCY_CHOICES),
            'cookie_name': CURRENCY_COOKIE_NAME,
            'signal': signals.currency_was_set
        },
        'language_code': {
            'choices': dict(settings.LANGUAGES),
            'cookie_name': settings.LANGUAGE_COOKIE_NAME,
            'signal': signals.language_was_set
        },
    }

    def post(self, request, *args, **kwargs):
        self.metasetting_keys = [key for key in self.parameters if key in self.request.POST]

        if self.metasetting_keys and 'redirect_url' in self.request.POST and 'submit' in self.request.POST:
            response = HttpResponseRedirect(self.request.POST.get('redirect_url'))

            cookies = {}

            for metasetting_key in self.metasetting_keys:
                code = self.request.POST.get(metasetting_key)
                key_params = self.parameters[metasetting_key]

                if code in key_params['choices']:

                    if key_params.get('signal', None):

                        results = key_params['signal'].send(**{'sender': request.__class__,
                                                               metasetting_key: code,
                                                               'request': request,
                                                               'parameters': self.request.POST})

                        for func, result in results:
                            if result and isinstance(result, HttpResponse):
                                response = result
                                break

                    cookies[key_params['cookie_name']] = code

            self.set_response_cookies(response, cookies)

            return response

        else:
            return self.get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'currency_labels': dict(CURRENCY_LABELS),
            'currency_choices': self.parameters['currency_code']['choices'],
            'currency_chunks': chunks(CURRENCY_CHOICES, 10),
            'path_info': request.POST.get('path_info', '/'),
            'status': kwargs.pop('status', 'language')
        })

    def set_response_cookies(self, response, cookies):
        cookie_domain = settings.SESSION_COOKIE_DOMAIN

        if cookie_domain and cookie_domain.startswith('.'):
            cookie_domain = cookie_domain % {'host': '.'.join(self.request.get_host().split('.')[-2:])}

        for k, v in cookies.items():
            set_cookie(response, k, v, cookie_domain=cookie_domain)

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(MetasettingsDashboard, self).dispatch(request, *args, **kwargs)


dashboard = MetasettingsDashboard.as_view()
