from __future__ import annotations

from django.http import HttpRequest


def get_client_ip(request: HttpRequest) -> str | None:
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ips = x_forwarded_for.split(",")

        for ip in ips:
            if "unknown" not in ip:
                return ip.strip()
    else:
        ip = request.META.get("REMOTE_ADDR")

    return ip
