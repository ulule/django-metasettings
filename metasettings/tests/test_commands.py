# -*- coding: utf-8 -*-
from __future__ import unicode_literals

try:
    from unittest import skipUnless
except:
    from django.utils.unittest import skipUnless

from datetime import date
from dateutil.relativedelta import relativedelta

from mock import patch

from django.test.client import RequestFactory
from django.core.management import call_command
from django.test import TestCase
from django.conf import settings

from metasettings.models import (CurrencyRate, convert_amount,
                                 CurrencyRateManager)
from metasettings.settings import CURRENCY_CHOICES


class CommandsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @skipUnless(settings.OPENEXCHANGERATES_APP_ID is not None, "OPENEXCHANGERATES_APP_ID not defined")
    def test_sync_rates(self):
        call_command('sync_rates', app_id=settings.OPENEXCHANGERATES_APP_ID)

        self.assertEqual(CurrencyRate.objects.filter(year__isnull=True, month__isnull=True).count(),
                         len(dict(CURRENCY_CHOICES).keys()))

    @skipUnless(settings.OPENEXCHANGERATES_APP_ID is not None, "OPENEXCHANGERATES_APP_ID not defined")
    def test_sync_rates_with_date_start(self):
        date_start = date.today()

        call_command('sync_rates',
                     app_id=settings.OPENEXCHANGERATES_APP_ID,
                     date_start=date_start.strftime('%Y-%m-%d'))

        self.assertEqual(CurrencyRate.objects.filter(year=date_start.year, month=date_start.month).count(),
                         len(dict(CURRENCY_CHOICES).keys()))

    @skipUnless(settings.OPENEXCHANGERATES_APP_ID is not None, "OPENEXCHANGERATES_APP_ID not defined")
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

    @skipUnless(settings.OPENEXCHANGERATES_APP_ID is not None, "OPENEXCHANGERATES_APP_ID not defined")
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
