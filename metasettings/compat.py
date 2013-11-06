import django


# Django 1.6+ compatibility
if django.VERSION >= (1, 6):
    from django.contrib.gis.geoip import GeoIP
else:
    from django.contrib.gis.utils import GeoIP


__all__ = ['GeoIP']
