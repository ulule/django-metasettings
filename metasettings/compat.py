import django


try:
    import geoip2  # noqa
except ImportError:
    has_geoip2 = False
else:
    has_geoip2 = True

if django.VERSION >= (2, 0) or has_geoip2:
    from django.contrib.gis.geoip2 import GeoIP2 as GeoIP  # noqa
# Django 1.6+ compatibility
elif django.VERSION >= (1, 6):
    from django.contrib.gis.geoip import GeoIP
else:
    from django.contrib.gis.utils import GeoIP


__all__ = ["GeoIP"]
