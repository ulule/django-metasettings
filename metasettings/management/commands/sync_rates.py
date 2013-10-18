import sys
import requests

from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from django.core.management.base import BaseCommand, CommandError

from optparse import make_option

from metasettings.models import CurrencyRate
from metasettings.settings import CURRENCY_CHOICES

try:
    import simplejson as json
except ImportError:
    import json  # NOQA


class Command(BaseCommand):
    can_import_settings = True

    option_list = BaseCommand.option_list + (
        make_option('--app_id',
                    dest='app_id',
                    default=None,
                    help='The openexchangerates APP ID'),

        make_option('--date_start',
                    dest='date_start',
                    default=None,
                    help='The date start to import currency rates'),

        make_option('--date_end',
                    dest='date_end',
                    default=None,
                    help='The date end to import currency rates'),
    )

    def handle(self, *args, **options):
        self.app_id = options.get('app_id', None)

        if not self.app_id:
            raise CommandError('The openexchangerates APP ID is required')

        start = options.get('date_start')
        end = options.get('date_end')

        if start is None and end is None:
            return self.rate_request()

        if start:
            start = datetime.strptime(options.get('date_start'), "%Y-%m-%d").date()
        else:
            start = date.today()

        if end:
            end = datetime.strptime(options.get('date_end'), "%Y-%m-%d").date()
        else:
            end = date.today()

        date_start = date(start.year, start.month, 1)
        date_end = date(end.year, end.month, 1)

        if date_start and date_end:
            current = date_start

            while date_end >= current:
                self.rate_request(current)

                current = current + relativedelta(months=1)

    def rate_request(self, current_date=None):
        url = 'http://openexchangerates.org'

        if current_date:
            url += '/api/historical/%s.json' % current_date.strftime("%Y-%m-%d")
        else:
            url += '/latest.json'

        response = requests.get(url, params={
            'app_id': self.app_id
        })

        if response.status_code == 200:
            result = json.loads(response.content)

            currency_choices = dict(CURRENCY_CHOICES)

            for currency, rate in result['rates'].iteritems():
                if not currency in currency_choices:
                    continue

                try:
                    filters = {
                        'currency': currency
                    }

                    if current_date:
                        filters.update({
                            'year': current_date.year,
                            'month': current_date.month
                        })

                    existing_rate = CurrencyRate.objects.get(**filters)

                    existing_rate.rate = str(existing_rate.rate)
                    rate = str("%.2f" % (rate))

                    if existing_rate.rate == rate:
                        continue
                    else:
                        existing_rate.rate = rate
                        existing_rate.save()

                        sys.stdout.write('Syncing currency %s with %s\n' % (currency, rate))

                except CurrencyRate.DoesNotExist:
                    currency_rate = CurrencyRate()
                    currency_rate.rate = str(rate)

                    for k, v in filters.items():
                        setattr(currency_rate, k, v)

                    currency_rate.save()

                    sys.stdout.write('Create currency %s with %s\n' % (currency, rate))
