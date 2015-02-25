from mock import patch

from datetime import date
from dateutil.relativedelta import relativedelta

from django.test import TestCase
from django.test.client import Client
from django.template import Context, Template
from django.core.management import call_command
from django.conf import settings
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse

from metasettings.models import (CurrencyRate, convert_amount,
                                 CurrencyRateManager,
                                 get_currency_from_ip_address)
from metasettings.settings import CURRENCY_CHOICES


class MetasettingsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_sync_rates(self):
        call_command('sync_rates', app_id=settings.OPENEXCHANGERATES_APP_ID)

        self.assertEqual(CurrencyRate.objects.filter(year__isnull=True, month__isnull=True).count(),
                         len(dict(CURRENCY_CHOICES).keys()))

    def test_sync_rates_with_date_start(self):
        date_start = date.today()

        call_command('sync_rates',
                     app_id=settings.OPENEXCHANGERATES_APP_ID,
                     date_start=date_start.strftime('%Y-%m-%d'))

        self.assertEqual(CurrencyRate.objects.filter(year=date_start.year, month=date_start.month).count(),
                         len(dict(CURRENCY_CHOICES).keys()))

    def test_sync_rates_with_date_start_and_date_end(self):
        months_count = 5

        dates = []

        date_end = date.today()

        date_start = date_end - relativedelta(months=months_count)

        for i in range(months_count):
            dates.append(date_start + relativedelta(months=i))

        call_command('sync_rates',
                     app_id=settings.OPENEXCHANGERATES_APP_ID,
                     date_start=date_start.strftime('%Y-%m-%d'),
                     date_end=date_end.strftime('%Y-%m-%d'))

        total = len(dict(CURRENCY_CHOICES).keys()) * months_count

        count = 0

        for current_date in dates:
            count += CurrencyRate.objects.filter(year=current_date.year,
                                                 month=current_date.month).count()

        self.assertEqual(count, total)

    def test_convert_amount(self):
        call_command('sync_rates', app_id=settings.OPENEXCHANGERATES_APP_ID)

        with patch.object(CurrencyRateManager, 'get_currency_rates') as get_currency_rates:
            get_currency_rates.return_value = {
                'EUR': CurrencyRate(rate=0.730862),
                'USD': CurrencyRate(rate=1)
            }

            amount = convert_amount('EUR', 'USD', 15, ceil=True)

            self.assertEqual(amount, 21)

            amount = convert_amount('EUR', 'USD', 15)

            self.assertEqual('%.2f' % amount, '20.52')

            amount = convert_amount('EUR', 'USD', 15, ceil=True)

            self.assertEqual(amount, 21)

            amount = convert_amount('EUR', 'USD', 15)

            self.assertEqual('%.2f' % amount, '20.52')

        amount = convert_amount('EUR', 'USD', 15, ceil=True, year=2011, month=10)

    def test_get_currency_from_ip_address(self):
        self.assertEqual(get_currency_from_ip_address('78.192.244.8'), 'EUR')  # France
        self.assertEqual(get_currency_from_ip_address('69.197.132.80'), 'USD')  # USA
        self.assertEqual(get_currency_from_ip_address('80.193.214.232'), 'GBP')  # United Kingdom
        self.assertEqual(get_currency_from_ip_address('218.75.205.72'), 'USD')  # China
        self.assertEqual(get_currency_from_ip_address('203.152.216.75'), 'JPY')  # Japan
        self.assertEqual(get_currency_from_ip_address('187.32.127.161'), 'BRL')  # Brasil

    def test_convert_amount_templatetags(self):
        with patch.object(CurrencyRateManager, 'get_currency_rates') as get_currency_rates:
            get_currency_rates.return_value = {
                'EUR': CurrencyRate(rate=0.730862),
                'USD': CurrencyRate(rate=1)
            }

            t = Template("{% load metasettings_tags %}{% convert_amount 'EUR' 'USD' 15 1 %}")
            result = t.render(Context())

            self.assertEqual(result, u'21')

            t = Template("{% load metasettings_tags %}{% convert_amount 'EUR' 'USD' 15 ceil=1 %}")
            result = t.render(Context())

            self.assertEqual(result, u'21')

            t = Template("{% load metasettings_tags %}{% convert_amount from_currency='EUR' to_currency='USD' amount=15 %}")
            result = t.render(Context())

            self.assertEqual(result, u'20.5237103585')

            t = Template("{% load metasettings_tags %}{% convert_amount 'EUR' 'USD' 15 ceil=1 as amount %}{{ amount }}")
            result = t.render(Context())

            self.assertEqual(result, u'21')

            t = Template("{% load metasettings_tags %}{% get_currency_from_request request as currency %}{{ currency }}")
            result = t.render(Context({
                'request': self.factory.get('/')
            }))

            self.assertEqual(result, u'EUR')

            t = Template("{% load metasettings_tags %}{% get_language_from_request request as lang %}{{ lang }}")
            result = t.render(Context({
                'request': self.factory.get('/')
            }))

            self.assertEqual(result, settings.LANGUAGE_CODE)

    def test_dashboard_view(self):
        client = Client()
        response = client.post(reverse('metasettings_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'metasettings/dashboard.html')

    def test_dashboard_complete(self):
        client = Client()
        response = client.post(reverse('metasettings_dashboard'), data={
            'submit': 1,
            'language_code': 'en',
            'currency_code': 'EUR',
            'redirect_url': '/'
        })

        self.assertEqual(response.status_code, 302)
