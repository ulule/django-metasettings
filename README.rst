===================
django-metasettings
===================

A reusable Django application to control the currency rate and favorite
language code, inspired by etsy

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

    python manage.py sync_rates --app_id=openexchangesratesappid


To import currency rates in a date range, run ::

    python manage.py sync_rates --app_id=openexchangesratesappid --date_start=2011-10-01 --date_end=2013-10-01

It will import for each months between the two dates the currency rates.


If you can to convert an amount from on currency to another ::

    from metasettings.models import convert_amount

    convert_amount('EUR', 'USD', 15)  # ~20 euros


By default it will return a full decimal, if you want a converted integer ::

    from metasettings.models import convert_amount

    convert_amount('EUR', 'USD', 15, ceil=True)  # ~20 euros


To retrieve the currency with a client IP Address::

    from metasettings.models import get_currency_from_ip_address

    get_currency_from_ip_address('78.192.244.8') # EUR

We are using `GeoIP`_ which gives you the ability to retrieve the country and
then we are linking the country to an existing currency.

So don't forget to import a fresh GeoIP database and be sure to have **GEOIP_PATH**
in your settings.

We recommend to use `django-geoip-utils <https://github.com/Gidsy/django-geoip-utils>`_
which provides some helpers to manipulate GeoIP API.

.. _GeoIP: https://docs.djangoproject.com/en/dev/ref/contrib/gis/geoip/
