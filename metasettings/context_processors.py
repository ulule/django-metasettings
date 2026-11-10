from __future__ import annotations

from typing import Any

from django.http import HttpRequest

from .choices import CURRENCY_CHOICES, CURRENCY_LABELS, TIMEZONE_CHOICES


def base(request: HttpRequest) -> dict[str, Any]:
    return {
        "CURRENCY_CHOICES": CURRENCY_CHOICES,
        "CURRENCY_LABELS": CURRENCY_LABELS,
        "TIMEZONE_CHOICES": TIMEZONE_CHOICES,
    }
