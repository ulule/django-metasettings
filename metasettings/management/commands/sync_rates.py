import sys

from django.core.management.base import BaseCommand

try:
    import simplejson as json
except ImportError:
    import json # NOQA


class Command(BaseCommand):
    def handle(self, *args, **options):
        import requests

        from metasettings.models import CurrencyRate
        from metasettings.choices import CURRENCY_CHOICES

        response = requests.get('http://openexchangerates.org/latest.json')

        if response.status_code == 200:
            result = json.loads(response.content)

            currency_rates = dict((currency_rate.currency, currency_rate) for currency_rate in CurrencyRate.objects.all())

            currency_choices = dict(CURRENCY_CHOICES)

            for currency, rate in result['rates'].iteritems():
                if not currency in currency_choices:
                    continue

                if currency in currency_rates:
                    current = currency_rates[currency]

                    if float(current.rate) == rate:
                        continue
                    else:
                        current.rate = str(rate)
                        current.save()

                        sys.stdout.write('Syncing currency %s with %s\n' % (currency, rate))
                else:
                    currency_rate = CurrencyRate()
                    currency_rate.rate = str(rate)
                    currency_rate.currency = currency
                    currency_rate.save()

                    sys.stdout.write('Creating currency %s with %s\n' % (currency, rate))
