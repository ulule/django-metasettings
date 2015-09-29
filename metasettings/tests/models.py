from django.db import models

from metasettings.fields import CurrencyField, TimezoneField


class Project(models.Model):
    name = models.CharField(max_length=100)
    currency = CurrencyField()
    timezone = TimezoneField()


class AllowNull(models.Model):
    currency = CurrencyField(null=True)
    timezone = TimezoneField(null=True)
