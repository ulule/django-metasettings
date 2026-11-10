from __future__ import annotations

import datetime
import logging
import math
import decimal
import pytz

from collections import defaultdict, OrderedDict
from collections.abc import Iterator, Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from django.utils import translation
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_str as force_str
from django.db import models
from django.http import HttpRequest

from . import settings, exceptions
from .helpers import get_client_ip
from .timezone import time_zone_by_country_and_region


logger = logging.getLogger("django.metasettings")

if TYPE_CHECKING:
    _CurrencyRateManagerBase = models.Manager["CurrencyRate"]
else:
    # Manager is only subscriptable at runtime since Django 3.1.
    _CurrencyRateManagerBase = models.Manager

_Money = TypeVar("_Money", bound="Money")


class Currencies(object):
    @cached_property
    def currencies(self) -> dict[str, str]:
        return dict(settings.CURRENCY_CHOICES)

    @cached_property
    def trigrams(self) -> dict[str, str]:
        return dict(settings.CURRENCY_TRIGRAMS)

    @cached_property
    def labels(self) -> dict[str, str]:
        return dict(settings.CURRENCY_LABELS)

    @cached_property
    def symbols(self) -> dict[str, str]:
        return dict(settings.CURRENCY_SYMBOLS)

    @cached_property
    def currency_by_countries(self) -> dict[str, str]:
        return dict(settings.CURRENCY_BY_COUNTRIES)

    def __iter__(self) -> Iterator[tuple[str, str]]:
        currencies = self.currencies

        for code, value in currencies.items():
            yield code, value

    @cached_property
    def countries(self) -> defaultdict[str, list[str]]:
        results: defaultdict[str, list[str]] = defaultdict(list)

        # Iterates the country codes only, so the unpacking splits each code in two letters: runtime behaviour kept.
        for country_code, currency_code in self.currency_by_countries:  # type: ignore[str-unpack]
            results[currency_code].append(country_code)

        return results

    def get_symbol(self, code: str | None) -> str:
        return self.symbols.get(code) or ""  # type: ignore[arg-type]

    def get_label(self, code: str | None) -> str:
        return self.labels.get(code) or ""  # type: ignore[arg-type]

    def get_trigram(self, code: str | None) -> str:
        return self.trigrams.get(code) or ""  # type: ignore[arg-type]

    def get_countries(self, code: str | None) -> list[str]:
        return self.countries.get(code) or []  # type: ignore[arg-type]

    def __bool__(self) -> bool:
        return bool(self.currencies)

    __nonzero__ = __bool__

    def __contains__(self, code: object) -> bool:
        return code in self.currencies


currencies: Currencies = Currencies()


class BaseObject(object):
    # None when the field is NULL: the descriptor wraps whatever is stored in the instance dict.
    code: str | None

    def __init__(self, code: str | None) -> None:
        self.code = code

    def __str__(self) -> str:
        return force_str(self.code or "")

    def __eq__(self, other: object) -> bool:
        return force_str(self) == force_str(other or "")

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(force_str(self))

    def __repr__(self) -> str:
        repr_text = "{0}(code={1})"

        return repr_text.format(self.__class__.__name__, repr(self.code))

    def __unicode__(self) -> str:
        return force_str(self.code or "")

    def __bool__(self) -> bool:
        return bool(self.code)

    def upper(self) -> str:
        # AttributeError when the code is None: runtime behaviour kept.
        return self.code.upper()  # type: ignore[union-attr]

    def encode(self, key: str) -> bytes:
        return force_str(self.code or "").encode(key)

    __nonzero__ = __bool__  # Python 2 compatibility.

    def __len__(self) -> int:
        return len(force_str(self))


class Currency(BaseObject):
    @property
    def symbol(self) -> str:
        return currencies.get_symbol(self.code)

    @property
    def label(self) -> str:
        return currencies.get_label(self.code)

    @property
    def trigram(self) -> str:
        return currencies.get_trigram(self.code)

    @property
    def countries(self) -> list[str]:
        return currencies.get_countries(self.code)

    @classmethod
    def from_ip_address(cls, ip_address: str | None) -> Currency:
        code: str | None = None

        try:
            from .compat import GeoIP
        except ImportError as e:
            logger.exception(e)
        else:
            try:
                # A None address raises and is logged below.
                code = GeoIP().country_code(ip_address)  # type: ignore[arg-type]
            except Exception as e:
                logger.warning(e)
            else:
                code = currencies.currency_by_countries.get(code, None)

        return cls(code or settings.DEFAULT_CURRENCY)

    @classmethod
    def from_cookies(cls, request: HttpRequest) -> Currency | None:
        code = request.COOKIES.get(settings.CURRENCY_COOKIE_NAME, None)

        if code is not None and code in currencies.currencies:
            return cls(code)

        return None

    @classmethod
    def from_request(cls, request: HttpRequest) -> Currency:
        currency = cls.from_cookies(request)

        if currency:
            return currency

        return cls.from_ip_address(get_client_ip(request))


def get_currency_from_request(request: HttpRequest) -> Currency:
    return Currency.from_request(request)


def get_currency_from_cookies(request: HttpRequest) -> Currency | None:
    return Currency.from_cookies(request)


def get_currency_from_ip_address(ip_address: str | None) -> Currency:
    return Currency.from_ip_address(ip_address)


def get_language_from_request(request: HttpRequest) -> str:
    return translation.get_language_from_request(request)


def convert_amount(
    from_currency: str | BaseObject | None,
    to_currency: str | BaseObject | None,
    amount: decimal.Decimal | int,
    ceil: bool = False,
    year: int | None = None,
    month: int | None = None,
) -> decimal.Decimal | int:
    if from_currency == to_currency:
        return amount

    # Keys are currency codes: a Currency hashes and compares equal to its code.
    currency_rates: Mapping[Any, CurrencyRate] = CurrencyRate.objects.get_currency_rates(
        year=year, month=month
    )

    result: decimal.Decimal | int = (amount / currency_rates[from_currency].rate) * currency_rates[
        to_currency
    ].rate

    if ceil:
        result = int(math.ceil(result))

    return result


class CurrencyRateManager(_CurrencyRateManagerBase):
    CURRENCY_CHOICES = dict(settings.CURRENCY_CHOICES)

    @cached_property
    def rates(self) -> defaultdict[Any, Any]:
        # Dynamic: year -> month -> currency -> rate, or currency -> rate when there is no date.
        rates: defaultdict[Any, Any] = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

        for currency_rate in self.all():
            if currency_rate.year and currency_rate.month:
                rates[currency_rate.year][currency_rate.month][
                    currency_rate.currency
                ] = currency_rate
            else:
                rates[currency_rate.currency] = currency_rate

        return rates

    @cached_property
    def default_rates(self) -> dict[str, CurrencyRate]:
        return dict(
            (currency_rate.currency, currency_rate)
            for currency_rate in self.filter(month__isnull=True, year__isnull=True)
        )

    def get_currency_rates(
        self, year: int | None = None, month: int | None = None
    ) -> dict[str, CurrencyRate]:
        if year and month:
            if year in self.rates and month in self.rates[year]:
                return self.rates[year][month]

        return self.default_rates

    def update_or_create(  # type: ignore[override]
        self, currency: str, rate: decimal.Decimal | float, date: datetime.date | None = None
    ) -> tuple[CurrencyRate, bool]:
        """Update a CurrencyRate object referenced by `currency` (and optionally
        `date`). If the object is not found, a new one will be created.

        Returns a tuple with the object and a `created` flag. If the object
        was neither updated nor created then None is returned.

        """
        try:
            filters: dict[str, Any] = {"currency": currency}
            if date:
                filters.update({"year": date.year, "month": date.month})

            existing_rate = CurrencyRate.objects.get(**filters)

            existing_rate.rate = str(existing_rate.rate)
            rate_text = str("%.2f" % (rate))

            if existing_rate.rate != rate_text:
                existing_rate.rate = rate_text
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
    currency = models.CharField(
        max_length=3, choices=settings.CURRENCY_LABELS, verbose_name=_("Currency")
    )

    rate = models.DecimalField(verbose_name=_("Rate"), max_digits=9, decimal_places=2)

    month = models.PositiveIntegerField(null=True, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)

    date_last_sync = models.DateTimeField(auto_now=True)

    objects = CurrencyRateManager()


class Money(object):
    __hash__ = None  # type: ignore[assignment]

    def __init__(
        self,
        amount: decimal.Decimal | int | str = "0",
        currency: str | BaseObject | None = None,
    ) -> None:
        try:
            self.amount = decimal.Decimal(amount)
        except decimal.InvalidOperation:
            raise ValueError(
                "amount value could not be converted to "
                "Decimal(): '{}'".format(amount)
            )
        self.currency = currency

    def __repr__(self) -> str:
        return "{} {}".format(self.currency, self.amount)

    def __str__(self) -> str:
        return force_str("{} {:,.2f}".format(self.currency, self.amount))

    def __lt__(self, other: Money | decimal.Decimal | int) -> bool:
        if isinstance(other, Money):
            if other.currency != self.currency:
                raise exceptions.CurrencyMismatch(self.currency, other.currency, "<")
            other = other.amount
        return self.amount < other

    def __le__(self, other: Money | decimal.Decimal | int) -> bool:
        if isinstance(other, Money):
            if other.currency != self.currency:
                raise exceptions.CurrencyMismatch(self.currency, other.currency, "<=")
            other = other.amount
        return self.amount <= other

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Money):
            return (self.amount == other.amount) and (self.currency == other.currency)
        return False

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __gt__(self, other: Money | decimal.Decimal | int) -> bool:
        if isinstance(other, Money):
            if other.currency != self.currency:
                raise exceptions.CurrencyMismatch(self.currency, other.currency, ">")
            other = other.amount
        return self.amount > other

    def __ge__(self, other: Money | decimal.Decimal | int) -> bool:
        if isinstance(other, Money):
            if other.currency != self.currency:
                raise exceptions.CurrencyMismatch(self.currency, other.currency, ">=")
            other = other.amount
        return self.amount >= other

    def __bool__(self) -> bool:
        return bool(self.amount)

    def __add__(self: _Money, other: _Money | decimal.Decimal | int) -> _Money:
        if isinstance(other, Money):
            if other.currency != self.currency:
                raise exceptions.CurrencyMismatch(self.currency, other.currency, "+")
            other = other.amount
        amount = self.amount + other
        return self.__class__(amount, self.currency)

    def __radd__(self: _Money, other: _Money | decimal.Decimal | int) -> _Money:
        return self.__add__(other)

    def __sub__(self: _Money, other: _Money | decimal.Decimal | int) -> _Money:
        if isinstance(other, Money):
            if other.currency != self.currency:
                raise exceptions.CurrencyMismatch(self.currency, other.currency, "-")
            other = other.amount
        amount = self.amount - other
        return self.__class__(amount, self.currency)

    def __rsub__(self: _Money, other: _Money | decimal.Decimal | int) -> _Money:
        return (-self).__add__(other)

    def __mul__(self: _Money, other: _Money | decimal.Decimal | int) -> _Money:
        if isinstance(other, Money):
            raise TypeError(
                "multiplication is unsupported between " "two money objects"
            )
        amount = self.amount * other
        return self.__class__(amount, self.currency)

    def __rmul__(self: _Money, other: _Money | decimal.Decimal | int) -> _Money:
        return self.__mul__(other)

    def __truediv__(self: _Money, other: _Money | decimal.Decimal | int) -> _Money | decimal.Decimal:
        if isinstance(other, Money):
            if other.currency != self.currency:
                raise exceptions.CurrencyMismatch(self.currency, other.currency, "/")

            if other.amount == 0:
                raise ZeroDivisionError()

            return self.amount / other.amount

        if other == 0:
            raise ZeroDivisionError()

        amount = self.amount / other

        return self.__class__(amount, self.currency)

    def __floordiv__(self: _Money, other: _Money | decimal.Decimal | int) -> _Money | decimal.Decimal:
        if isinstance(other, Money):
            if other.currency != self.currency:
                raise exceptions.CurrencyMismatch(self.currency, other.currency, "//")

            if other.amount == 0:
                raise ZeroDivisionError()
            return self.amount // other.amount

        if other == 0:
            raise ZeroDivisionError()

        amount = self.amount // other
        return self.__class__(amount, self.currency)

    def __mod__(self: _Money, other: _Money | decimal.Decimal | int) -> _Money:
        if isinstance(other, Money):
            raise TypeError(
                "modulo is unsupported between two '{}' "
                "objects".format(self.__class__.__name__)
            )
        if other == 0:
            raise ZeroDivisionError()

        amount = self.amount % other
        return self.__class__(amount, self.currency)

    def __divmod__(
        self: _Money, other: _Money | decimal.Decimal | int
    ) -> tuple[decimal.Decimal, decimal.Decimal] | tuple[_Money, _Money]:
        if isinstance(other, Money):
            if other.currency != self.currency:
                raise exceptions.CurrencyMismatch(
                    self.currency, other.currency, "divmod"
                )

            if other.amount == 0:
                raise ZeroDivisionError()

            return divmod(self.amount, other.amount)

        if other == 0:
            raise ZeroDivisionError()

        whole, remainder = divmod(self.amount, other)

        return (
            self.__class__(whole, self.currency),
            self.__class__(remainder, self.currency),
        )

    def __pow__(self: _Money, other: _Money | decimal.Decimal | int) -> _Money:
        if isinstance(other, Money):
            raise TypeError(
                "power operator is unsupported between two '{}' "
                "objects".format(self.__class__.__name__)
            )
        amount = self.amount ** other
        return self.__class__(amount, self.currency)

    def __neg__(self: _Money) -> _Money:
        return self.__class__(-self.amount, self.currency)

    def __pos__(self: _Money) -> _Money:
        return self.__class__(+self.amount, self.currency)

    def __abs__(self: _Money) -> _Money:
        return self.__class__(abs(self.amount), self.currency)

    def __int__(self) -> int:
        return int(self.amount)

    def __float__(self) -> float:
        return float(self.amount)

    def __round__(self: _Money, ndigits: int = 0) -> _Money:
        return self.__class__(round(self.amount, ndigits), self.currency)

    def to(
        self: _Money, currency: str | BaseObject | None, ceil: bool = False
    ) -> _Money:
        """Return equivalent money object in another currency"""
        if currency == self.currency or currency is None:
            return self

        amount = convert_amount(self.currency, currency, self.amount, ceil=ceil)

        return self.__class__(amount, currency)


class Timezones(object):
    @cached_property
    def timezones(self) -> OrderedDict[str, str]:
        return OrderedDict(settings.TIMEZONE_CHOICES)

    def __iter__(self) -> Iterator[tuple[str, str]]:
        timezones = self.timezones

        for code, value in timezones.items():
            yield code, value

    def __bool__(self) -> bool:
        return bool(self.timezones)

    __nonzero__ = __bool__

    def __contains__(self, code: object) -> bool:
        return code in self.timezones


timezones: Timezones = Timezones()


class Timezone(BaseObject):
    @classmethod
    def from_ip_address(cls, ip_address: str | None) -> Timezone:
        if not ip_address:
            return cls(settings.TIME_ZONE)

        zone = settings.TIME_ZONE

        try:
            from .compat import GeoIP
        except ImportError as e:
            logger.exception(e)
        else:
            try:
                data = GeoIP().city(ip_address)
            except Exception as e:
                logger.warning(e)
            else:
                if data:
                    zone = time_zone_by_country_and_region(
                        data["country_code"], data["region"] or ""
                    )
        return cls(zone)

    @classmethod
    def from_request(cls, request: HttpRequest) -> Timezone:
        zone = request.COOKIES.get(settings.TIMEZONE_COOKIE_NAME, None)

        if zone is not None and zone in timezones.timezones:
            return cls(zone)

        return cls.from_ip_address(get_client_ip(request))

    @property
    def value(self) -> pytz.BaseTzInfo | None:
        if self.code:
            return pytz.timezone(self.code)
        return None


def get_timezone_from_request(request: HttpRequest) -> Timezone:
    return Timezone.from_request(request)


def get_timezone_from_ip_address(ip_address: str | None) -> Timezone:
    return Timezone.from_ip_address(ip_address)
