# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'Bad_User_Patterns'
        db.delete_table('watchdog_bad_user_patterns')

        # Deleting model 'Site_Health'
        db.delete_table('watchdog_site_health')

        # Adding model 'BadUserPattern'
        db.create_table('watchdog_baduserpattern', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pattern', self.gf('django.db.models.fields.CharField')(max_length=30)),
        ))
        db.send_create_signal('watchdog', ['BadUserPattern'])

        # Adding model 'SiteHealth'
        db.create_table('watchdog_sitehealth', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('datestamp', self.gf('django.db.models.fields.DateTimeField')()),
            ('extra', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal('watchdog', ['SiteHealth'])


    def backwards(self, orm):
        
        # Adding model 'Bad_User_Patterns'
        db.create_table('watchdog_bad_user_patterns', (
            ('pattern', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('watchdog', ['Bad_User_Patterns'])

        # Adding model 'Site_Health'
        db.create_table('watchdog_site_health', (
            ('datestamp', self.gf('django.db.models.fields.DateTimeField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('extra', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal('watchdog', ['Site_Health'])

        # Deleting model 'BadUserPattern'
        db.delete_table('watchdog_baduserpattern')

        # Deleting model 'SiteHealth'
        db.delete_table('watchdog_sitehealth')


    models = {
        'watchdog.baduserpattern': {
            'Meta': {'object_name': 'BadUserPattern'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pattern': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'watchdog.sitehealth': {
            'Meta': {'object_name': 'SiteHealth'},
            'datestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'extra': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['watchdog']
