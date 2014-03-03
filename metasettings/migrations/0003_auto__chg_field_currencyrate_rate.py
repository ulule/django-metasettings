# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'CurrencyRate.rate'
        db.alter_column(u'metasettings_currencyrate', 'rate', self.gf('django.db.models.fields.DecimalField')(max_digits=7, decimal_places=2))

    def backwards(self, orm):

        # Changing field 'CurrencyRate.rate'
        db.alter_column(u'metasettings_currencyrate', 'rate', self.gf('django.db.models.fields.DecimalField')(max_digits=5, decimal_places=2))

    models = {
        u'metasettings.currencyrate': {
            'Meta': {'object_name': 'CurrencyRate'},
            'currency': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'date_last_sync': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'month': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'rate': ('django.db.models.fields.DecimalField', [], {'max_digits': '7', 'decimal_places': '2'}),
            'year': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['metasettings']