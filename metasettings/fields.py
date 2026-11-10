from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Generic, TypeVar, TYPE_CHECKING, overload

from django.db import models
from django.db.models.expressions import Combinable
from django.db.models.fields import BLANK_CHOICE_DASH
from django.utils.encoding import force_str as force_str
from django.utils.functional import lazy

from .models import (
    Currencies,
    Currency,
    Timezone,
    Timezones,
    currencies,
    timezones,
)

# __set__ value type
_ST = TypeVar("_ST", contravariant=True)
# __get__ return type
_GT = TypeVar("_GT", covariant=True)

if TYPE_CHECKING:

    class _CharField(models.CharField[_ST, _GT]):
        pass

else:
    # CharField is only subscriptable for the type checker: re-declare it as generic at runtime.
    class _CharField(models.CharField, Generic[_ST, _GT]):
        pass


class BaseDescriptor(object):
    def __init__(self, field: BaseChoiceField[Any, Any]) -> None:
        self.field = field

    def __set__(self, instance: models.Model, value: object) -> None:
        if value is not None:
            value = force_str(value)
        instance.__dict__[self.field.name] = value


class CurrencyDescriptor(BaseDescriptor):
    @overload
    def __get__(self, instance: None, owner: type[Any] | None = None) -> CurrencyDescriptor: ...

    @overload
    def __get__(self, instance: models.Model, owner: type[Any] | None = None) -> Currency: ...

    def __get__(
        self, instance: models.Model | None = None, owner: type[Any] | None = None
    ) -> Currency | CurrencyDescriptor:
        return Currency(code=instance.__dict__[self.field.name]) if instance else self


class TimezoneDescriptor(BaseDescriptor):
    @overload
    def __get__(self, instance: None, owner: type[Any] | None = None) -> TimezoneDescriptor: ...

    @overload
    def __get__(self, instance: models.Model, owner: type[Any] | None = None) -> Timezone: ...

    def __get__(
        self, instance: models.Model | None = None, owner: type[Any] | None = None
    ) -> Timezone | TimezoneDescriptor:
        return Timezone(code=instance.__dict__[self.field.name]) if instance else self


class BaseChoiceField(_CharField[_ST, _GT]):
    descriptor_class: type[BaseDescriptor]
    blank_label: str | None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.blank_label = kwargs.pop("blank_label", None)
        return super(BaseChoiceField, self).__init__(*args, **kwargs)

    def get_internal_type(self) -> str:
        return "CharField"

    def contribute_to_class(  # type: ignore[override]
        self, cls: type[models.Model], name: str
    ) -> None:
        super(BaseChoiceField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, self.descriptor_class(self))

    def get_choices(  # type: ignore[override]
        self,
        include_blank: bool = True,
        blank_choice: list[tuple[str, str]] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> Any:  # lazy() proxy of a list, see below
        if blank_choice is None:
            if self.blank_label is None:
                blank_choice = BLANK_CHOICE_DASH
            else:
                blank_choice = [("", self.blank_label)]
        return super(BaseChoiceField, self).get_choices(  # type: ignore[misc]
            include_blank=include_blank, blank_choice=blank_choice, *args, **kwargs
        )

    def get_prep_value(self, value: object) -> str | None:
        "Returns field's value prepared for saving into a database."
        # Convert the Currency to unicode for database insertion.
        if value is None or getattr(value, "code", "") is None:
            return None
        return force_str(value)

    def get_prep_lookup(self, lookup_type: str, value: object) -> Any:
        if hasattr(value, "code"):
            value = value.code

        # Field.get_prep_lookup() no longer exists in recent Django versions.
        return super(BaseChoiceField, self).get_prep_lookup(  # type: ignore[misc]
            lookup_type, value
        )

    get_choices = lazy(get_choices, list)


class CurrencyField(BaseChoiceField[_ST, _GT]):
    # The descriptor stores force_str(value) and always hands back a Currency wrapper,
    # including for null=True fields (Currency(code=None)): never Optional.
    _pyi_private_set_type: str | Currency | Combinable  # type: ignore[assignment]
    _pyi_private_get_type: Currency  # type: ignore[assignment]
    # Currency compares equal to its code, and the lookup value is unwrapped to its code.
    _pyi_lookup_exact_type: Any

    descriptor_class = CurrencyDescriptor
    currencies: Currencies

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        currencies_class = kwargs.pop("currencies", None)
        self.currencies = currencies_class() if currencies_class else currencies

        kwargs.update({"choices": self.currencies, "max_length": 3})

        return super(CurrencyField, self).__init__(*args, **kwargs)

    def deconstruct(self) -> tuple[str, str, Sequence[Any], dict[str, Any]]:
        name, path, args, kwargs = super(CurrencyField, self).deconstruct()
        kwargs.pop("choices")
        if self.currencies is not currencies:
            # Include the countries class if it's not the default countries
            # instance.
            kwargs["currencies"] = self.currencies.__class__
        return name, path, args, kwargs


class TimezoneField(BaseChoiceField[_ST, _GT]):
    # Same as CurrencyField: always a Timezone wrapper, Timezone(code=None) when NULL.
    _pyi_private_set_type: str | Timezone | Combinable  # type: ignore[assignment]
    _pyi_private_get_type: Timezone  # type: ignore[assignment]
    _pyi_lookup_exact_type: Any

    descriptor_class = TimezoneDescriptor
    timezones: Timezones

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        timezones_class = kwargs.pop("timezones", None)
        self.timezones = timezones_class() if timezones_class else timezones
        kwargs.update({"max_length": 63, "choices": self.timezones})
        super(TimezoneField, self).__init__(*args, **kwargs)

    def deconstruct(self) -> tuple[str, str, Sequence[Any], dict[str, Any]]:
        name, path, args, kwargs = super(TimezoneField, self).deconstruct()
        if kwargs["choices"] == self.timezones:
            del kwargs["choices"]
        if kwargs["max_length"] == 63:
            del kwargs["max_length"]

        return name, path, args, kwargs
