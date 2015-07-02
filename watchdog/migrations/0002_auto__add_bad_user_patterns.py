# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Bad_User_Patterns'
        db.create_table('watchdog_bad_user_patterns', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pattern', self.gf('django.db.models.fields.CharField')(max_length=30)),
        ))
        db.send_create_signal('watchdog', ['Bad_User_Patterns'])


    def backwards(self, orm):
        
        # Deleting model 'Bad_User_Patterns'
        db.delete_table('watchdog_bad_user_patterns')


    models = {
        'watchdog.bad_user_patterns': {
            'Meta': {'object_name': 'Bad_User_Patterns'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pattern': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'watchdog.site_health': {
            'Meta': {'object_name': 'Site_Health'},
            'datestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'extra': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['watchdog']
