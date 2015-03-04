from django.db import models

from metasettings.fields import CurrencyField


class Project(models.Model):
    currency = CurrencyField()
