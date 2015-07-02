# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'LogHistory'
        db.create_table('logger_loghistory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('logger', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('execution_date_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('detail_dict', self.gf('django.db.models.fields.TextField')(max_length=2000, null=True, blank=True)),
        ))
        db.send_create_signal('logger', ['LogHistory'])


    def backwards(self, orm):
        
        # Deleting model 'LogHistory'
        db.delete_table('logger_loghistory')


    models = {
        'logger.loghistory': {
            'Meta': {'object_name': 'LogHistory'},
            'detail_dict': ('django.db.models.fields.TextField', [], {'max_length': '2000', 'null': 'True', 'blank': 'True'}),
            'execution_date_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logger': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '150'})
        }
    }

    complete_apps = ['logger']
