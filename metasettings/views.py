from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from . import signals
from .util import set_cookie, chunks
from .settings import CURRENCY_COOKIE_NAME, CURRENCY_LABELS, CURRENCY_CHOICES


@require_POST
@csrf_exempt
def dashboard(request, status=None):
    currency_choices = dict(CURRENCY_CHOICES)

    if 'submit' in request.POST and 'redirect_url' in request.POST:
        cookie_domain = settings.SESSION_COOKIE_DOMAIN

        if cookie_domain and cookie_domain.startswith('.'):
            cookie_domain = cookie_domain % {'host': '.'.join(request.get_host().split('.')[-2:])}

        parameters = request.POST

        response = HttpResponseRedirect(parameters.get('redirect_url'))

        keys = {
            'currency_code': {
                'choices': currency_choices,
                'cookie_name': CURRENCY_COOKIE_NAME,
                'signal': signals.currency_was_set
            },
            'language_code': {
                'choices': dict(settings.LANGUAGES),
                'cookie_name': settings.LANGUAGE_COOKIE_NAME,
                'signal': signals.language_was_set
            }
        }

        cookies = {}

        for key, value in keys.items():
            if key in parameters and parameters.get(key) in value['choices']:
                code = parameters.get(key)

                kwargs = {
                    'sender': request.__class__,
                    key: code,
                    'request': request,
                    'parameters': parameters
                }

                results = value['signal'].send(**kwargs)

                for func, result in results:
                    if result and isinstance(result, HttpResponse):
                        response = result
                        break

                cookies[value['cookie_name']] = code

        for k, v in cookies.items():
            set_cookie(response, k, v, cookie_domain=cookie_domain)

        return response

    return render(request, 'metasettings/dashboard.html', {
        'currency_labels': dict(CURRENCY_LABELS),
        'currency_choices': currency_choices,
        'currency_chunks': chunks(CURRENCY_CHOICES, 10),
        'path_info': request.POST.get('path_info', '/'),
        'status': status or 'language'
    })
