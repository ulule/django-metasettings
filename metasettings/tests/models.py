from django.db import models

from metasettings.fields import CurrencyField


class Project(models.Model):
    name = models.CharField(max_length=100)
    currency = CurrencyField()


class AllowNull(models.Model):
    currency = CurrencyField(null=True)
