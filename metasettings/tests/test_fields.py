# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.encoding import force_text
from django.forms import Select
from django.forms.models import modelform_factory
from django.test import TestCase

from .models import Project, AllowNull

from metasettings.fields import Currency, Timezone


class FieldTests(TestCase):
    def test_assign_with_trigram(self):
        project = Project(currency='USD')

        assert project.currency.symbol == '$'
        assert project.currency.label == 'United States Dollar'
        assert project.currency.trigram == 'USD'
        assert project.currency.code == 'USD'

    def test_assign_without_trigram(self):
        project = Project(currency='EUR')

        assert project.currency.symbol == '€'
        assert project.currency.label == 'Euro'
        assert project.currency.trigram == ''
        assert project.currency.code == 'EUR'

    def test_text(self):
        project = Project(currency='EUR', timezone='Europe/Paris')
        assert force_text(project.currency) == 'EUR'
        assert force_text(project.timezone) == 'Europe/Paris'

    def test_blank(self):
        project = Project.objects.create(name='thoas one')
        self.assertEqual(project.currency, '')
        self.assertEqual(project.timezone, '')

        project = Project.objects.get(pk=project.pk)
        project.currency == ''
        project.timezone == ''

    def test_null(self):
        obj = AllowNull.objects.create(currency=None, timezone=None)
        self.assertIsNone(obj.currency.code)
        self.assertIsNone(obj.timezone.code)

        obj = AllowNull.objects.get(pk=obj.pk)
        self.assertIsNone(obj.currency.code)
        self.assertIsNone(obj.timezone.code)

    def test_len(self):
        project = Project(currency='EUR', timezone='Europe/Paris')
        self.assertEqual(len(project.currency), 3)
        self.assertEqual(len(project.timezone), 12)

    def test_lookup(self):
        Project.objects.create(name='one', currency='EUR', timezone='Europe/Paris')
        Project.objects.create(name='two', currency='USD', timezone='America/Detroit')
        Project.objects.create(name='three', currency='EUR', timezone='Europe/Paris')

        lookup = Project.objects.filter(currency='EUR')
        names = lookup.order_by('name').values_list('name', flat=True)
        self.assertEqual(list(names), ['one', 'three'])

        lookup = Project.objects.filter(timezone='Europe/Paris')
        names = lookup.order_by('name').values_list('name', flat=True)
        self.assertEqual(list(names), ['one', 'three'])

    def test_lookup_currency_timezone(self):
        Project.objects.create(name='one', currency='EUR', timezone='Europe/Paris')
        Project.objects.create(name='two', currency='USD', timezone='America/Detroit')
        Project.objects.create(name='three', currency='EUR', timezone='Europe/Paris')

        currency = Currency('EUR')

        timezone = Timezone('Europe/Paris')

        lookup = Project.objects.filter(currency=currency)
        names = lookup.order_by('name').values_list('name', flat=True)
        self.assertEqual(list(names), ['one', 'three'])

        lookup = Project.objects.filter(timezone=timezone)
        names = lookup.order_by('name').values_list('name', flat=True)
        self.assertEqual(list(names), ['one', 'three'])

    def test_create_modelform(self):
        Form = modelform_factory(Project, fields=['currency'])
        form_field = Form().fields['currency']
        self.assertTrue(isinstance(form_field.widget, Select))

    def test_render_form(self):
        Form = modelform_factory(Project, fields=['currency'])
        Form().as_p()
