# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from mock import patch

from django.test import TestCase
from django.test.client import Client
from django.template import Context, Template
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory

from metasettings.models import (CurrencyRate,
                                 CurrencyRateManager,
                                 get_currency_from_ip_address)


class ModelTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

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

            self.assertEqual(result, '21')

            t = Template("{% load metasettings_tags %}{% convert_amount 'EUR' 'USD' 15 ceil=1 %}")
            result = t.render(Context())

            self.assertEqual(result, '21')

            t = Template("{% load metasettings_tags %}{% convert_amount from_currency='EUR' to_currency='USD' amount=15 %}")
            result = t.render(Context())

            self.assertEqual(round(float(result), 2), 20.52)

            t = Template("{% load metasettings_tags %}{% convert_amount 'EUR' 'USD' 15 ceil=1 as amount %}{{ amount }}")
            result = t.render(Context())

            self.assertEqual(result, '21')

            t = Template("{% load metasettings_tags %}{% get_currency_from_request request as currency %}{{ currency }}")
            result = t.render(Context({
                'request': self.factory.get('/')
            }))

            self.assertEqual(result, 'EUR')

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
