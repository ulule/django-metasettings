import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

SITE_ID = 1
DEBUG = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'metasettings',
    'metasettings.tests',
]

SECRET_KEY = 'blabla'

OPENEXCHANGERATES_APP_ID = os.getenv('OPENEXCHANGERATES_APP_ID')

GEOIP_PATH = os.path.join(os.path.dirname(__file__), 'data', 'GeoIP.dat')
