===================
django-metasettings
===================

.. image:: https://secure.travis-ci.org/thoas/django-metasettings.png?branch=master
    :alt: Build Status
    :target: http://travis-ci.org/thoas/django-metasettings

A reusable Django application to control the currency rate and favorite
language code, inspired by etsy.

First you need to request an app id at
`open exchange rates <https://openexchangerates.org/>`_ to import currency rates.

Installation
------------

1. To install it, simply ::

    pip install django-metasettings

2. Add 'metasettings' to your ``INSTALLED_APPS`` ::

    INSTALLED_APPS = (
        'metasettings',
    )

If you want to install the dashboard to allow your users to select a language
and a currency you will have to install urls from metasettings like so ::

    # urls.py

    from django.conf.urls import patterns, include

    urlpatterns = patterns(
        '',
        (r'^', include('metasettings.urls'))
    )

You can add your proper stylesheet to this dashboard view and have this kind
of result:

.. image:: http://cl.ly/image/2j0I3V1B0G1w/metasettings.png


Usage
-----

To import current currency rates, run ::

    $ python manage.py sync_rates --app_id=openexchangesratesappid


To import currency rates in a date range, run ::

    $ python manage.py sync_rates --app_id=openexchangesratesappid --date_start=2011-10-01 --date_end=2013-10-01

It will import for each months between the two dates the currency rates.

The OpenExchangeRates app id can also be stored in the
``OPENEXCHANGERATES_APP_ID`` Django setting.

If you can to convert an amount from on currency to another:

.. code-block:: python

    from metasettings.models import convert_amount

    convert_amount('EUR', 'USD', 15)  # ~20 euros


By default it will return a full decimal, if you want a converted integer:

.. code-block:: python

    from metasettings.models import convert_amount

    convert_amount('EUR', 'USD', 15, ceil=True)  # ~20 euros


To retrieve the currency with a client IP Address:

.. code-block:: python

    from metasettings.models import get_currency_from_ip_address

    get_currency_from_ip_address('78.192.244.8') # EUR

We are using `GeoIP`_ which gives you the ability to retrieve the country and
then we are linking the country to an existing currency.

So don't forget to import a fresh GeoIP database and be sure to have **GEOIP_PATH**
in your settings.

We recommend to use `django-geoip-utils <https://github.com/thoas/django-geoip-utils>`_
which provides some helpers to manipulate GeoIP API.

CurrencyField
-------------

A currency field for Django models that provides all ISO 4217 currencies as choices.

``CurrencyField`` is based on Django's ``CharField``, providing choices
corresponding to the official ISO 4217 list of currencies (with a default
``max_length`` of 3).

Consider the following model using a ``CurrencyField``:

.. code-block:: python

    from django.db import models

    from metasettings.fields import CurrencyField

    class Project(models.Model):
        name = models.CharField(max_length=100)
        currency = CurrencyField()

Any ``Project`` instance will have a ``currency`` attribute that you can use to
get details of the project's currency:

.. code-block:: python

    >>> project = Project(name='My project', currency='EUR')
    >>> project.currency
    Currency(code='EUR')
    >>> project.currency.label
    'Euro'
    >>> project.currency.symbol
    '€'
    >>> project = Project(name='My project', currency='USD')
    >>> project.currency
    Currency(code='USD')
    >>> project.currency.label
    'United States Dollar'
    >>> project.currency.symbol
    '$'
    >>> project.currency.trigram
    'USD'

This object (``project.currency`` in the example) is a ``Currency`` instance,
which is described below.

Use ``blank_label`` to set the label for the initial blank choice shown in
forms::

    currency = CurrencyField(blank_label='(select currency)')

Roadmap
-------

see `issues <https://github.com/thoas/django-metasettings/issues>`_

This application only includes major currencies, don't hesitate to send
patch or improvements.

Inspirations
------------

* The ``CurrencyField`` is heavily inspired from ``CountryField`` of the great `django-countries`_

.. _GeoIP: https://docs.djangoproject.com/en/dev/ref/contrib/gis/geoip/
.. _django-countries: https://github.com/SmileyChris/django-countries
