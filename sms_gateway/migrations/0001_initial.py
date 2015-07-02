# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'SMSMessage'
        db.create_table('sms_gateway_smsmessage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('smsid', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True)),
            ('smsto', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('smsfrom', self.gf('django.db.models.fields.CharField')(max_length=16, null=True, blank=True)),
            ('mobile_phone', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['subscriber.MobilePhone'], null=True)),
            ('note', self.gf('django.db.models.fields.CharField')(max_length=160, null=True, blank=True)),
            ('subaccount', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('report', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, max_length=1, null=True, blank=True)),
            ('vp', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('sms_gateway', ['SMSMessage'])

        # Adding model 'SMSMessageSent'
        db.create_table('sms_gateway_smsmessagesent', (
            ('smsmessage_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['sms_gateway.SMSMessage'], unique=True, primary_key=True)),
            ('smsmsg', self.gf('django.db.models.fields.TextField')(max_length=800)),
            ('flash', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('split', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, max_length=1)),
            ('smsudh', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('sent_datetime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('sms_gateway', ['SMSMessageSent'])

        # Adding model 'SMSMessageReceived'
        db.create_table('sms_gateway_smsmessagereceived', (
            ('smsmessage_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['sms_gateway.SMSMessage'], unique=True, primary_key=True)),
            ('smsdate', self.gf('django.db.models.fields.DateTimeField')()),
            ('network', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('smsmsg', self.gf('django.db.models.fields.CharField')(max_length=160)),
            ('bits', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=7, max_length=2)),
            ('smsc', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('smsudh', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('smsucs2', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('received_datetime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('sms_gateway', ['SMSMessageReceived'])

        # Adding model 'SMSReport'
        db.create_table('sms_gateway_smsreport', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('smsfrom', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('smsdate', self.gf('django.db.models.fields.DateTimeField')()),
            ('smsmsg', self.gf('django.db.models.fields.CharField')(max_length=160)),
            ('reason', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('smsid', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sms_gateway.SMSMessageSent'])),
            ('status', self.gf('django.db.models.fields.CharField')(max_length='14')),
        ))
        db.send_create_signal('sms_gateway', ['SMSReport'])

        # Adding model 'SMSResponse'
        db.create_table('sms_gateway_smsresponse', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sms_gateway.SMSMessageSent'])),
            ('received', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sms_gateway.SMSMessageReceived'])),
            ('response_direction', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('is_opt_out', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('sms_gateway', ['SMSResponse'])


    def backwards(self, orm):
        
        # Deleting model 'SMSMessage'
        db.delete_table('sms_gateway_smsmessage')

        # Deleting model 'SMSMessageSent'
        db.delete_table('sms_gateway_smsmessagesent')

        # Deleting model 'SMSMessageReceived'
        db.delete_table('sms_gateway_smsmessagereceived')

        # Deleting model 'SMSReport'
        db.delete_table('sms_gateway_smsreport')

        # Deleting model 'SMSResponse'
        db.delete_table('sms_gateway_smsresponse')


    models = {
        'geolocation.coordinate': {
            'Meta': {'object_name': 'Coordinate'},
            'cos_rad_lat': ('django.db.models.fields.FloatField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {}),
            'longitude': ('django.db.models.fields.FloatField', [], {}),
            'rad_lat': ('django.db.models.fields.FloatField', [], {}),
            'rad_lon': ('django.db.models.fields.FloatField', [], {}),
            'sin_rad_lat': ('django.db.models.fields.FloatField', [], {})
        },
        'geolocation.uscity': {
            'Meta': {'object_name': 'USCity'},
            'coordinate': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geolocation.Coordinate']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '33'}),
            'us_county': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geolocation.USCounty']"}),
            'us_state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geolocation.USState']"})
        },
        'geolocation.uscounty': {
            'Meta': {'object_name': 'USCounty'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'us_state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geolocation.USState']"})
        },
        'geolocation.usstate': {
            'Meta': {'object_name': 'USState'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '24'})
        },
        'geolocation.uszip': {
            'Meta': {'object_name': 'USZip'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '5'}),
            'coordinate_id': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'us_city': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geolocation.USCity']"}),
            'us_county': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geolocation.USCounty']"}),
            'us_state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geolocation.USState']"})
        },
        'market.site': {
            'Meta': {'object_name': 'Site'},
            'base_rate': ('django.db.models.fields.DecimalField', [], {'default': '0', 'null': 'True', 'max_digits': '6', 'decimal_places': '0', 'blank': 'True'}),
            'broadcaster_allotment': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'default_state_province': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'default_state_province'", 'null': 'True', 'to': "orm['geolocation.USState']"}),
            'default_zip_postal': ('django.db.models.fields.CharField', [], {'max_length': '9', 'null': 'True', 'blank': 'True'}),
            'directory_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inactive_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'launch_date': ('django.db.models.fields.DateField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'market_cities': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'phase': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'short_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '22'}),
            'us_city': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['geolocation.USCity']", 'null': 'True', 'blank': 'True'}),
            'us_county': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['geolocation.USCounty']", 'null': 'True', 'blank': 'True'}),
            'us_state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geolocation.USState']", 'null': 'True', 'blank': 'True'}),
            'us_zip': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['geolocation.USZip']", 'null': 'True', 'blank': 'True'})
        },
        'sms_gateway.smsmessage': {
            'Meta': {'object_name': 'SMSMessage'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mobile_phone': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['subscriber.MobilePhone']", 'null': 'True'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'}),
            'report': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'smsfrom': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'smsid': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'smsto': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'subaccount': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'vp': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'sms_gateway.smsmessagereceived': {
            'Meta': {'object_name': 'SMSMessageReceived', '_ormbases': ['sms_gateway.SMSMessage']},
            'bits': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '7', 'max_length': '2'}),
            'network': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'received_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'response': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['sms_gateway.SMSMessageSent']", 'through': "orm['sms_gateway.SMSResponse']"}),
            'smsc': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'smsdate': ('django.db.models.fields.DateTimeField', [], {}),
            'smsmessage_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['sms_gateway.SMSMessage']", 'unique': 'True', 'primary_key': 'True'}),
            'smsmsg': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'smsucs2': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'smsudh': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        'sms_gateway.smsmessagesent': {
            'Meta': {'object_name': 'SMSMessageSent', '_ormbases': ['sms_gateway.SMSMessage']},
            'flash': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'sent_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'smsmessage_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['sms_gateway.SMSMessage']", 'unique': 'True', 'primary_key': 'True'}),
            'smsmsg': ('django.db.models.fields.TextField', [], {'max_length': '800'}),
            'smsudh': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'split': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'max_length': '1'})
        },
        'sms_gateway.smsreport': {
            'Meta': {'object_name': 'SMSReport'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reason': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'smsdate': ('django.db.models.fields.DateTimeField', [], {}),
            'smsfrom': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'smsid': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sms_gateway.SMSMessageSent']"}),
            'smsmsg': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': "'14'"})
        },
        'sms_gateway.smsresponse': {
            'Meta': {'object_name': 'SMSResponse'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_opt_out': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'received': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sms_gateway.SMSMessageReceived']"}),
            'response_direction': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'sent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sms_gateway.SMSMessageSent']"})
        },
        'subscriber.carrier': {
            'Meta': {'object_name': 'Carrier'},
            'carrier': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'carrier_display_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_major_carrier': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'site': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'site'", 'to': "orm['market.Site']"}),
            'user_name': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'})
        },
        'subscriber.mobilephone': {
            'Meta': {'object_name': 'MobilePhone'},
            'carrier': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['subscriber.Carrier']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mobile_phone_number': ('django.contrib.localflavor.us.models.PhoneNumberField', [], {'unique': 'True', 'max_length': '20'})
        }
    }

    complete_apps = ['sms_gateway']
