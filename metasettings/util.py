import datetime

from django.conf import settings


def set_cookie(response, key, value, days_expire=7, cookie_domain=None):
    if days_expire is None:
        max_age = 365 * 24 * 60 * 60  # one year
    else:
        max_age = days_expire * 24 * 60 * 60

    expires = datetime.datetime.strftime(datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age), '%a, %d-%b-%Y %H:%M:%S GMT')

    response.set_cookie(key,
                        value,
                        max_age=max_age,
                        expires=expires,
                        domain=cookie_domain or settings.SESSION_COOKIE_DOMAIN,
                        secure=settings.SESSION_COOKIE_SECURE or None)

    return response


def chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i + n]
