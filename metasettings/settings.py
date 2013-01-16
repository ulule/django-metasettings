from django.conf import settings


METASETTINGS_CURRENCY_COOKIE_NAME = getattr(settings, 'METASETTINGS_CURRENCY_COOKIE_NAME', 'django_currency')

METASETTINGS_DEFAULT_CURRENCY = getattr(settings, 'METASETTINGS_DEFAULT_CURRENCY', 'EUR')
