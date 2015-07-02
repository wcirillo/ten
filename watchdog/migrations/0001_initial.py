# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Site_Health'
        db.create_table('watchdog_site_health', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('datestamp', self.gf('django.db.models.fields.DateTimeField')()),
            ('extra', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal('watchdog', ['Site_Health'])


    def backwards(self, orm):
        
        # Deleting model 'Site_Health'
        db.delete_table('watchdog_site_health')


    models = {
        'watchdog.site_health': {
            'Meta': {'object_name': 'Site_Health'},
            'datestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'extra': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['watchdog']
