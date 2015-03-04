from __future__ import unicode_literals

from collections import defaultdict

from django.db import models
from django.db.models.fields import BLANK_CHOICE_DASH
from django.utils.encoding import force_text, python_2_unicode_compatible
from django.utils.functional import lazy, cached_property

from . import settings


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

    def __iter__(self):
        currencies = self.currencies

        for code, value in currencies.items():
            yield code, value

    @cached_property
    def countries(self):
        results = defaultdict(list)

        for country_code, currency_code in settings.CURRENCY_BY_COUNTRIES:
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
class Currency(object):
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

    def __bool__(self):
        return bool(self.code)

    __nonzero__ = __bool__   # Python 2 compatibility.

    def __len__(self):
        return len(force_text(self))

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


class CurrencyDescriptor(object):
    def __init__(self, field):
        self.field = field

    def __get__(self, instance=None, owner=None):
        if instance is None:
            raise AttributeError(
                "The '%s' attribute can only be accessed from %s instances."
                % (self.field.name, owner.__name__))
        return Currency(
            code=instance.__dict__[self.field.name],
        )

    def __set__(self, instance, value):
        if value is not None:
            value = force_text(value)
        instance.__dict__[self.field.name] = value


class CurrencyField(models.CharField):
    descriptor_class = CurrencyDescriptor

    def __init__(self, *args, **kwargs):
        currencies_class = kwargs.pop('currencies', None)
        self.currencies = currencies_class() if currencies_class else currencies
        self.blank_label = kwargs.pop('blank_label', None)

        kwargs.update({
            'choices': self.currencies,
            'max_length': 3
        })

        return super(CurrencyField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return "CharField"

    def contribute_to_class(self, cls, name):
        super(CurrencyField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, self.descriptor_class(self))

    def get_prep_value(self, value):
        "Returns field's value prepared for saving into a database."
        # Convert the Currency to unicode for database insertion.
        if value is None or getattr(value, 'code', '') is None:
            return None
        return force_text(value)

    def get_prep_lookup(self, lookup_type, value):
        if hasattr(value, 'code'):
            value = value.code

        return super(CurrencyField, self).get_prep_lookup(lookup_type, value)

    def get_choices(
            self, include_blank=True, blank_choice=None, *args, **kwargs):
        if blank_choice is None:
            if self.blank_label is None:
                blank_choice = BLANK_CHOICE_DASH
            else:
                blank_choice = [('', self.blank_label)]
        return super(CurrencyField, self).get_choices(
            include_blank=include_blank, blank_choice=blank_choice, *args,
            **kwargs)

    get_choices = lazy(get_choices, list)

    def deconstruct(self):
        name, path, args, kwargs = super(CurrencyField, self).deconstruct()
        kwargs.pop('choices')
        if self.currencies is not currencies:
            # Include the countries class if it's not the default countries
            # instance.
            kwargs['currencies'] = self.currencies.__class__
        return name, path, args, kwargs


try:  # pragma: no cover
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ['^metasettings\.fields\.CurrencyField'])
except ImportError:
    pass
