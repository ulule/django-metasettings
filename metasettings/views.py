from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .choices import CURRENCY_LABELS, CURRENCY_CHOICES
from . import signals
from .util import set_cookie, chunks
from .settings import METASETTINGS_CURRENCY_COOKIE_NAME


@require_POST
@csrf_exempt
def dashboard(request, status=None):
    currency_choices = dict(CURRENCY_CHOICES)

    if 'submit' in request.POST:
        cookie_domain = settings.SESSION_COOKIE_DOMAIN

        if cookie_domain and cookie_domain.startswith('.'):
            cookie_domain = cookie_domain % {'host': '.'.join(request.get_host().split('.')[-2:])}

        response = HttpResponseRedirect(request.POST.get('redirect_url'))

        if 'currency_code' in request.POST and request.POST.get('currency_code') in currency_choices:

            currency_code = request.POST.get('currency_code')

            signals.currency_was_set.send(
                sender=request.__class__,
                currency_code=currency_code,
                request=request
            )

            set_cookie(response, METASETTINGS_CURRENCY_COOKIE_NAME, currency_code, cookie_domain=cookie_domain)

        if 'language_code' in request.POST and request.POST.get('language_code') in dict(settings.LANGUAGES):

            language_code = request.POST.get('language_code')

            signals.language_was_set.send(
                sender=request.__class__,
                language_code=language_code,
                request=request
            )

            if hasattr(request, 'session'):
                request.session['django_language'] = language_code

            set_cookie(response, settings.LANGUAGE_COOKIE_NAME, language_code, cookie_domain=cookie_domain)

            return response

    return render(request, 'metasettings/dashboard.html', {
        'currency_labels': dict(CURRENCY_LABELS),
        'currency_choices': currency_choices,
        'currency_chunks': chunks(CURRENCY_CHOICES, 10),
        'path_info': request.POST.get('path_info', '/'),
        'status': status or 'language'
    })
