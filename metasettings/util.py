from __future__ import annotations

import datetime
from typing import Iterator, Sequence, TypeVar

from django.conf import settings
from django.http.response import HttpResponseBase

_T = TypeVar("_T")
_R = TypeVar("_R", bound=HttpResponseBase)


def set_cookie(
    response: _R,
    key: str,
    value: str,
    days_expire: int | None = 7,
    cookie_domain: str | None = None,
) -> _R:
    if days_expire is None:
        max_age = 365 * 24 * 60 * 60  # one year
    else:
        max_age = days_expire * 24 * 60 * 60

    expires = datetime.datetime.strftime(
        datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age),
        "%a, %d-%b-%Y %H:%M:%S GMT",
    )

    response.set_cookie(
        key,
        value,
        max_age=max_age,
        expires=expires,
        domain=cookie_domain or settings.SESSION_COOKIE_DOMAIN,
        secure=settings.SESSION_COOKIE_SECURE or None,  # type: ignore[arg-type]
    )

    return response


def chunks(l: Sequence[_T], n: int) -> Iterator[Sequence[_T]]:
    # xrange does not exist on Python 3 (NameError when iterated): runtime behaviour kept.
    for i in xrange(0, len(l), n):  # type: ignore[name-defined]
        yield l[i : i + n]
