import logging
import math
import decimal
import pytz

from collections import defaultdict, OrderedDict

from django.utils import translation
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text, python_2_unicode_compatible
from django.db import models

from . import settings, exceptions
from .helpers import get_client_ip
from .timezone import time_zone_by_country_and_region


class Currencies(object):
    @cached_property
    def currencies(self):
        return dict(settings.CURRENCY_CHOICES)

    @cached_property
    def trigrams(self):
        return dict(settings.CURRENCY_TRIGRAMS)

    @cached_property
    def labels(self):
        return dict(settings.CURRENCY_LABELS)

    @cached_property
    def symbols(self):
        return dict(settings.CURRENCY_SYMBOLS)

    @cached_property
    def currency_by_countries(self):
        return dict(settings.CURRENCY_BY_COUNTRIES)

    def __iter__(self):
        currencies = self.currencies

        for code, value in currencies.items():
            yield code, value

    @cached_property
    def countries(self):
        results = defaultdict(list)

        for country_code, currency_code in self.currency_by_countries:
            results[currency_code].append(country_code)

        return results

    def get_symbol(self, code):
        return self.symbols.get(code) or ''

    def get_label(self, code):
        return self.labels.get(code) or ''

    def get_trigram(self, code):
        return self.trigrams.get(code) or ''

    def get_countries(self, code):
        return self.countries.get(code) or []

    def __bool__(self):
        return bool(self.currencies)

    __nonzero__ = __bool__

    def __contains__(self, code):
        return code in self.currencies


currencies = Currencies()


@python_2_unicode_compatible
class BaseObject(object):
    def __init__(self, code):
        self.code = code

    def __str__(self):
        return force_text(self.code or '')

    def __eq__(self, other):
        return force_text(self) == force_text(other or '')

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(force_text(self))

    def __repr__(self):
        repr_text = "{0}(code={1})"

        return repr_text.format(
            self.__class__.__name__, repr(self.code))

    def __unicode__(self):
        return force_text(self.code or '')

    def __bool__(self):
        return bool(self.code)

    def upper(self):
        return self.code.upper()

    def encode(self, key):
        return force_text(self.code or '').encode(key)

    __nonzero__ = __bool__   # Python 2 compatibility.

    def __len__(self):
        return len(force_text(self))


class Currency(BaseObject):
    @property
    def symbol(self):
        return currencies.get_symbol(self.code)

    @property
    def label(self):
        return currencies.get_label(self.code)

    @property
    def trigram(self):
        return currencies.get_trigram(self.code)

    @property
    def countries(self):
        return currencies.get_countries(self.code)

    @classmethod
    def from_ip_address(cls, ip_address):
        code = None

        try:
            from .compat import GeoIP
        except ImportError as e:
            logging.info(e)
        else:
            code = GeoIP().country_code(ip_address)

            code = currencies.currency_by_countries.get(code, None)

        return cls(code or settings.DEFAULT_CURRENCY)

    @classmethod
    def from_cookies(cls, request):
        code = request.COOKIES.get(settings.CURRENCY_COOKIE_NAME, None)

        if code is not None and code in currencies.currencies:
            return cls(code)

        return None

    @classmethod
    def from_request(cls, request):
        code = cls.from_cookies(request)

        if code:
            return code

        return cls.from_ip_address(get_client_ip(request))


def get_currency_from_request(request):
    return Currency.from_request(request)


def get_currency_from_cookies(request):
    return Currency.from_cookies(request)


def get_currency_from_ip_address(ip_address):
    return Currency.from_ip_address(ip_address)


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
    CURRENCY_CHOICES = dict(settings.CURRENCY_CHOICES)

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

    def update_or_create(self, currency, rate, date=None):
        """Update a CurrencyRate object referenced by `currency` (and optionally
        `date`). If the object is not found, a new one will be created.

        Returns a tuple with the object and a `created` flag. If the object
        was neither updated nor created then None is returned.

        """
        try:
            filters = {'currency': currency}
            if date:
                filters.update({
                    'year': date.year,
                    'month': date.month
                })

            existing_rate = CurrencyRate.objects.get(**filters)

            existing_rate.rate = str(existing_rate.rate)
            rate = str("%.2f" % (rate))

            if existing_rate.rate != rate:
                existing_rate.rate = rate
                existing_rate.save()
            return existing_rate, False

        except CurrencyRate.DoesNotExist:
            currency_rate = CurrencyRate()
            currency_rate.rate = str(rate)

            for k, v in filters.items():
                setattr(currency_rate, k, v)

            currency_rate.save()

            return currency_rate, True


class CurrencyRate(models.Model):
    currency = models.CharField(max_length=3,
                                choices=settings.CURRENCY_LABELS,
                                verbose_name=_('Currency'))

    rate = models.DecimalField(verbose_name=_('Rate'),
                               max_digits=7,
                               decimal_places=2)

    month = models.PositiveIntegerField(null=True, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)

    date_last_sync = models.DateTimeField(auto_now=True)

    objects = CurrencyRateManager()


@python_2_unicode_compatible
class Money(object):
    __hash__ = None

    def __init__(self, amount="0", currency=None):
        try:
            self.amount = decimal.Decimal(amount)
        except decimal.InvalidOperation:
            raise ValueError("amount value could not be converted to "
                             "Decimal(): '{}'".format(amount))
        self.currency = currency

    def __repr__(self):
        return "{} {}".format(self.currency, self.amount)

    def __str__(self):
        return force_text("{} {:,.2f}".format(self.currency, self.amount))

    def __lt__(self, other):
        if isinstance(other, Money):
            if other.currency != self.currency:
                raise exceptions.CurrencyMismatch(self.currency, other.currency, '<')
            other = other.amount
        return self.amount < other

    def __le__(self, other):
        if isinstance(other, Money):
            if other.currency != self.currency:
                raise exceptions.CurrencyMismatch(self.currency, other.currency, '<=')
            other = other.amount
        return self.amount <= other

    def __eq__(self, other):
        if isinstance(other, Money):
            return ((self.amount == other.amount) and
                    (self.currency == other.currency))
        return False

    def __ne__(self, other):
        return not self == other

    def __gt__(self, other):
        if isinstance(other, Money):
            if other.currency != self.currency:
                raise exceptions.CurrencyMismatch(self.currency, other.currency, '>')
            other = other.amount
        return self.amount > other

    def __ge__(self, other):
        if isinstance(other, Money):
            if other.currency != self.currency:
                raise exceptions.CurrencyMismatch(self.currency, other.currency, '>=')
            other = other.amount
        return self.amount >= other

    def __bool__(self):
        return bool(self.amount)

    def __add__(self, other):
        if isinstance(other, Money):
            if other.currency != self.currency:
                raise exceptions.CurrencyMismatch(self.currency, other.currency, '+')
            other = other.amount
        amount = self.amount + other
        return self.__class__(amount, self.currency)

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, Money):
            if other.currency != self.currency:
                raise exceptions.CurrencyMismatch(self.currency, other.currency, '-')
            other = other.amount
        amount = self.amount - other
        return self.__class__(amount, self.currency)

    def __rsub__(self, other):
        return (-self).__add__(other)

    def __mul__(self, other):
        if isinstance(other, Money):
            raise TypeError("multiplication is unsupported between "
                            "two money objects")
        amount = self.amount * other
        return self.__class__(amount, self.currency)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, Money):
            if other.currency != self.currency:
                raise exceptions.CurrencyMismatch(self.currency, other.currency, '/')

            if other.amount == 0:
                raise ZeroDivisionError()

            return self.amount / other.amount

        if other == 0:
            raise ZeroDivisionError()

        amount = self.amount / other

        return self.__class__(amount, self.currency)

    def __floordiv__(self, other):
        if isinstance(other, Money):
            if other.currency != self.currency:
                raise exceptions.CurrencyMismatch(self.currency, other.currency, '//')

            if other.amount == 0:
                raise ZeroDivisionError()
            return self.amount // other.amount

        if other == 0:
            raise ZeroDivisionError()

        amount = self.amount // other
        return self.__class__(amount, self.currency)

    def __mod__(self, other):
        if isinstance(other, Money):
            raise TypeError("modulo is unsupported between two '{}' "
                            "objects".format(self.__class__.__name__))
        if other == 0:
            raise ZeroDivisionError()

        amount = self.amount % other
        return self.__class__(amount, self.currency)

    def __divmod__(self, other):
        if isinstance(other, Money):
            if other.currency != self.currency:
                raise exceptions.CurrencyMismatch(self.currency, other.currency, 'divmod')

            if other.amount == 0:
                raise ZeroDivisionError()

            return divmod(self.amount, other.amount)

        if other == 0:
            raise ZeroDivisionError()

        whole, remainder = divmod(self.amount, other)

        return (self.__class__(whole, self.currency),
                self.__class__(remainder, self.currency))

    def __pow__(self, other):
        if isinstance(other, Money):
            raise TypeError("power operator is unsupported between two '{}' "
                            "objects".format(self.__class__.__name__))
        amount = self.amount ** other
        return self.__class__(amount, self.currency)

    def __neg__(self):
        return self.__class__(-self.amount, self.currency)

    def __pos__(self):
        return self.__class__(+self.amount, self.currency)

    def __abs__(self):
        return self.__class__(abs(self.amount), self.currency)

    def __int__(self):
        return int(self.amount)

    def __float__(self):
        return float(self.amount)

    def __round__(self, ndigits=0):
        return self.__class__(round(self.amount, ndigits), self.currency)

    def to(self, currency, ceil=False):
        """Return equivalent money object in another currency"""
        if currency == self.currency or currency is None:
            return self

        amount = convert_amount(self.currency, currency, self.amount, ceil=ceil)

        return self.__class__(amount, currency)


class Timezones(object):
    @cached_property
    def timezones(self):
        return OrderedDict(settings.TIMEZONE_CHOICES)

    def __iter__(self):
        timezones = self.timezones

        for code, value in timezones.items():
            yield code, value

    def __bool__(self):
        return bool(self.timezones)

    __nonzero__ = __bool__

    def __contains__(self, code):
        return code in self.timezones


timezones = Timezones()


class Timezone(BaseObject):
    @classmethod
    def from_ip_address(cls, ip_address):
        if not ip_address:
            return cls(settings.TIME_ZONE)
        try:
            from .compat import GeoIP
        except ImportError as e:
            logging.info(e)
        else:
            data = GeoIP().city(ip_address)
            zone = None
            if data:
                zone = time_zone_by_country_and_region(data['country_code'],
                                                       data['region'] or '')
        return cls(zone or settings.TIME_ZONE)

    @classmethod
    def from_request(cls, request):
        zone = request.COOKIES.get(settings.TIMEZONE_COOKIE_NAME, None)

        if zone is not None and zone in timezones.timezones:
            return cls(zone)

        return cls.from_ip_address(get_client_ip(request))

    @property
    def value(self):
        if self.code:
            return pytz.timezone(self.code)
        return None


def get_timezone_from_request(request):
    return Timezone.from_request(request)


def get_timezone_from_ip_address(ip_address):
    return Timezone.from_ip_address(ip_address)
