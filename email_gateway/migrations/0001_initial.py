# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Scheduled_Task'
        db.create_table('email_gateway_scheduled_task', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('url_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('email_gateway', ['Scheduled_Task'])

        # Adding model 'ScheduledTask_Status'
        db.create_table('email_gateway_scheduledtask_status', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('task', self.gf('django.db.models.fields.related.ForeignKey')(related_name='scheduled_tasks', to=orm['email_gateway.Scheduled_Task'])),
            ('success', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('data', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('time', self.gf('django.db.models.fields.TimeField')(auto_now_add=True)),
        ))
        db.send_create_signal('email_gateway', ['ScheduledTask_Status'])

        # Adding unique constraint on 'ScheduledTask_Status', fields ['task', 'date']
        db.create_unique('email_gateway_scheduledtask_status', ['task_id', 'date'])


    def backwards(self, orm):
        
        # Deleting model 'Scheduled_Task'
        db.delete_table('email_gateway_scheduled_task')

        # Deleting model 'ScheduledTask_Status'
        db.delete_table('email_gateway_scheduledtask_status')

        # Removing unique constraint on 'ScheduledTask_Status', fields ['task', 'date']
        db.delete_unique('email_gateway_scheduledtask_status', ['task_id', 'date'])


    models = {
        'email_gateway.scheduled_task': {
            'Meta': {'object_name': 'Scheduled_Task'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'url_name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'email_gateway.scheduledtask_status': {
            'Meta': {'unique_together': "(('task', 'date'),)", 'object_name': 'ScheduledTask_Status'},
            'data': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'success': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'scheduled_tasks'", 'to': "orm['email_gateway.Scheduled_Task']"}),
            'time': ('django.db.models.fields.TimeField', [], {'auto_now_add': 'True'})
        }
    }

    complete_apps = ['email_gateway']
