import logging
import math

from django.utils import translation
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.db import models
from django.utils.functional import memoize

from metasettings.settings import CURRENCY_COOKIE_NAME, METASETTINGS_DEFAULT_CURRENCY
from metasettings.choices import CURRENCY_BY_COUNTRIES, CURRENCY_LABELS


def get_currency_from_request(request):
    currency_code = request.COOKIES.get(getattr(settings, 'CURRENCY_COOKIE_NAME', CURRENCY_COOKIE_NAME), None)

    if not currency_code:
        currency_code = get_currency_from_ip_address(request.META['REMOTE_ADDR'])

    return currency_code or getattr(settings, 'METASETTINGS_DEFAULT_CURRENCY', METASETTINGS_DEFAULT_CURRENCY)


def get_currency_from_ip_address(ip_address):
    currency_code = None

    try:
        from django.contrib.gis.utils import GeoIP
    except ImportError, e:
        logging.info(e)
    else:
        g = GeoIP()
        country = g.country(ip_address)

        currency_by_countries = dict(CURRENCY_BY_COUNTRIES)

        if 'country_code' in country and country['country_code'] in currency_by_countries:
            currency_code = currency_by_countries.get(country['country_code'], None)

    return currency_code


def get_language_from_request(request):
    return translation.get_language_from_request(request)


def convert_amount(from_currency, to_currency, amount, ceil=False):
    if from_currency == to_currency:
        return amount

    currency_rates = get_currency_rates()

    result = (amount / currency_rates[from_currency]['rate']) * currency_rates[to_currency]['rate']

    if ceil:
        result = int(math.ceil(result))

    return result


def _get_currency_rates():
    return dict((currency_rate['currency'], currency_rate)
                for currency_rate in CurrencyRate.objects.values('currency', 'rate'))


get_currency_rates = memoize(_get_currency_rates, {}, 0)


class CurrencyRate(models.Model):
    currency = models.CharField(max_length=3, choices=CURRENCY_LABELS, verbose_name=_('Currency'))
    rate = models.DecimalField(verbose_name=_(u'Rate'), max_digits=5, decimal_places=2)

    date_last_sync = models.DateTimeField(auto_now_add=True, auto_now=True)
