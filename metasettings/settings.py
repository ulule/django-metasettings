from django.conf import settings

from . import choices


CURRENCY_COOKIE_NAME = getattr(
    settings, "METASETTINGS_CURRENCY_COOKIE_NAME", "django_currency"
)

TIMEZONE_COOKIE_NAME = getattr(
    settings, "METASETTINGS_CURRENCY_TIMEZONE_NAME", "django_timezone"
)

DEFAULT_CURRENCY = getattr(settings, "METASETTINGS_DEFAULT_CURRENCY", "EUR")

CURRENCY_CHOICES = getattr(
    settings, "METASETTINGS_CURRENCY_CHOICES", choices.CURRENCY_CHOICES
)

CURRENCY_TRIGRAMS = getattr(
    settings, "METASETTINGS_CURRENCY_TRIGRAMS", choices.CURRENCY_TRIGRAMS
)

CURRENCY_LABELS = getattr(
    settings, "METASETTINGS_CURRENCY_LABELS", choices.CURRENCY_LABELS
)

CURRENCY_BY_COUNTRIES = getattr(
    settings, "METASETTINGS_CURRENCY_BY_COUNTRIES", choices.CURRENCY_BY_COUNTRIES
)

CURRENCY_SYMBOLS = getattr(
    settings, "METASETTINGS_CURRENCY_SYMBOLS", choices.CURRENCY_SYMBOLS
)

TIMEZONE_CHOICES = getattr(
    settings, "METASETTINGS_TIMEZONE_CHOICES", choices.TIMEZONE_CHOICES
)

TIME_ZONE = getattr(
    settings,
    "METASETTINGS_TIME_ZONE",
    getattr(settings, "TIME_ZONE", choices.TIME_ZONE),
)
