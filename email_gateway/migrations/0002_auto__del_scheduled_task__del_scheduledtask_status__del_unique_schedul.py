# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Removing unique constraint on 'ScheduledTask_Status', fields ['task', 'date']
        db.delete_unique('email_gateway_scheduledtask_status', ['task_id', 'date'])

        # Deleting model 'Scheduled_Task'
        db.delete_table('email_gateway_scheduled_task')

        # Deleting model 'ScheduledTask_Status'
        db.delete_table('email_gateway_scheduledtask_status')

        # Adding model 'Email'
        db.create_table('email_gateway_email', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=120)),
            ('message', self.gf('django.db.models.fields.TextField')()),
            ('email_subscription', self.gf('django.db.models.fields.related.ForeignKey')(default=6, related_name='emails', to=orm['consumer.EmailSubscription'])),
            ('user_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('draft_email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
            ('create_datetime', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('send_datetime', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('send_status', self.gf('django.db.models.fields.IntegerField')(default=0, max_length=1)),
            ('num_recipients', self.gf('django.db.models.fields.IntegerField')(default=-1)),
        ))
        db.send_create_signal('email_gateway', ['Email'])


    def backwards(self, orm):
        
        # Adding model 'Scheduled_Task'
        db.create_table('email_gateway_scheduled_task', (
            ('url_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('email_gateway', ['Scheduled_Task'])

        # Adding model 'ScheduledTask_Status'
        db.create_table('email_gateway_scheduledtask_status', (
            ('task', self.gf('django.db.models.fields.related.ForeignKey')(related_name='scheduled_tasks', to=orm['email_gateway.Scheduled_Task'])),
            ('success', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('time', self.gf('django.db.models.fields.TimeField')(auto_now_add=True)),
            ('date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('data', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('email_gateway', ['ScheduledTask_Status'])

        # Adding unique constraint on 'ScheduledTask_Status', fields ['task', 'date']
        db.create_unique('email_gateway_scheduledtask_status', ['task_id', 'date'])

        # Deleting model 'Email'
        db.delete_table('email_gateway_email')


    models = {
        'consumer.emailsubscription': {
            'Meta': {'object_name': 'EmailSubscription'},
            'email_subscription_name': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'email_gateway.email': {
            'Meta': {'ordering': "['-create_datetime']", 'object_name': 'Email'},
            'create_datetime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'draft_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'email_subscription': ('django.db.models.fields.related.ForeignKey', [], {'default': '6', 'related_name': "'emails'", 'to': "orm['consumer.EmailSubscription']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'num_recipients': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'send_datetime': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'send_status': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '1'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '120'}),
            'user_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"})
        }
    }

    complete_apps = ['email_gateway']
