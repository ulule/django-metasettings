import logging
import math

from collections import defaultdict

from django.utils import translation
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.db import models

from . import settings


def get_currency_from_request(request):
    currency_code = request.COOKIES.get(settings.CURRENCY_COOKIE_NAME, None)

    if not currency_code:
        currency_code = get_currency_from_ip_address(request.META['REMOTE_ADDR'])

    return currency_code or settings.DEFAULT_CURRENCY


def get_currency_from_ip_address(ip_address):
    currency_code = None

    try:
        from .compat import GeoIP
    except ImportError, e:
        logging.info(e)
    else:
        g = GeoIP()
        country = g.country(ip_address)

        currency_by_countries = dict(settings.CURRENCY_BY_COUNTRIES)

        if 'country_code' in country and country['country_code'] in currency_by_countries:
            currency_code = currency_by_countries.get(country['country_code'], None)

    return currency_code


def get_language_from_request(request):
    return translation.get_language_from_request(request)


def convert_amount(from_currency, to_currency, amount, ceil=False,
                   year=None, month=None):
    if from_currency == to_currency:
        return amount

    currency_rates = CurrencyRate.objects.get_currency_rates(year=year, month=month)

    result = (amount / currency_rates[from_currency].rate) * currency_rates[to_currency].rate

    if ceil:
        result = int(math.ceil(result))

    return result


class CurrencyRateManager(models.Manager):
    @cached_property
    def rates(self):
        rates = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

        for currency_rate in self.all():
            if currency_rate.year and currency_rate.month:
                rates[currency_rate.year][currency_rate.month][currency_rate.currency] = currency_rate
            else:
                rates[currency_rate.currency] = currency_rate

        return rates

    @cached_property
    def default_rates(self):
        return dict((currency_rate.currency, currency_rate)
                    for currency_rate in self.filter(month__isnull=True, year__isnull=True))

    def get_currency_rates(self, year=None, month=None):
        if year and month:
            if year in self.rates and month in self.rates[year]:
                return self.rates[year][month]

        return self.default_rates


class CurrencyRate(models.Model):
    currency = models.CharField(max_length=3, choices=settings.CURRENCY_LABELS, verbose_name=_('Currency'))
    rate = models.DecimalField(verbose_name=_(u'Rate'), max_digits=7, decimal_places=2)

    month = models.PositiveIntegerField(null=True, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)

    date_last_sync = models.DateTimeField(auto_now_add=True, auto_now=True)

    objects = CurrencyRateManager()
