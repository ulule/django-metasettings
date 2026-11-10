"""Static checks only (run by mypy, never imported): what the model fields read as."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import assert_type

    from metasettings.models import Currency, Timezone

    from .models import AllowNull, Project

    def check_fields(project: Project, nullable: AllowNull) -> None:
        assert_type(project.currency, Currency)
        assert_type(project.timezone, Timezone)
        assert_type(project.currency.code, "str | None")

        # Both a code and a wrapper can be assigned.
        project.currency = "EUR"
        project.currency = project.currency
        project.timezone = "Europe/Paris"
        Project(currency="EUR", timezone=Timezone("Europe/Paris"))

        # The django-stubs plugin widens null=True fields to Optional, whereas the descriptor
        # always returns a wrapper (Currency(code=None) when the column is NULL).
        assert_type(nullable.currency, "Currency | None")
        nullable.currency = None
