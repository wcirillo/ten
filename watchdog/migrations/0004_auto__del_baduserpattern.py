# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'BadUserPattern'
        db.delete_table('watchdog_baduserpattern')


    def backwards(self, orm):
        
        # Adding model 'BadUserPattern'
        db.create_table('watchdog_baduserpattern', (
            ('pattern', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('watchdog', ['BadUserPattern'])


    models = {
        'watchdog.sitehealth': {
            'Meta': {'object_name': 'SiteHealth'},
            'datestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'extra': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['watchdog']
