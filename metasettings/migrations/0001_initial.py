# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CurrencyRate'
        db.create_table(u'metasettings_currencyrate', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('currency', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('rate', self.gf('django.db.models.fields.DecimalField')(max_digits=5, decimal_places=2)),
            ('date_last_sync', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'metasettings', ['CurrencyRate'])


    def backwards(self, orm):
        # Deleting model 'CurrencyRate'
        db.delete_table(u'metasettings_currencyrate')


    models = {
        u'metasettings.currencyrate': {
            'Meta': {'object_name': 'CurrencyRate'},
            'currency': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'date_last_sync': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rate': ('django.db.models.fields.DecimalField', [], {'max_digits': '5', 'decimal_places': '2'})
        }
    }

    complete_apps = ['metasettings']