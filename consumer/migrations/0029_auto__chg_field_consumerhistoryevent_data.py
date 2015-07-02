# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'ConsumerHistoryEvent.data'
        db.alter_column('consumer_consumerhistoryevent', 'data', self.gf('django.db.models.fields.CharField')(max_length=250, null=True))


    def backwards(self, orm):
        
        # Changing field 'ConsumerHistoryEvent.data'
        db.alter_column('consumer_consumerhistoryevent', 'data', self.gf('django.db.models.fields.CharField')(max_length=50, null=True))


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'consumer.baduserpattern': {
            'Meta': {'object_name': 'BadUserPattern'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pattern': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'consumer.consumer': {
            'Meta': {'object_name': 'Consumer', '_ormbases': ['auth.User']},
            'consumer_create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'consumer_modified_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'consumer_zip_postal': ('django.db.models.fields.CharField', [], {'max_length': '9', 'null': 'True', 'blank': 'True'}),
            'email_hash': ('django.db.models.fields.CharField', [], {'max_length': '42', 'null': 'True', 'blank': 'True'}),
            'email_subscription': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'consumers'", 'blank': 'True', 'to': "orm['consumer.EmailSubscription']"}),
            'geolocation_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'geolocation_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'is_email_verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_emailable': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'nomail_reason': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'consumers'", 'blank': 'True', 'to': "orm['consumer.UnEmailableReason']"}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'default': '1', 'related_name': "'consumers'", 'to': "orm['market.Site']"}),
            'subscriber': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'subscribers'", 'unique': 'True', 'null': 'True', 'to': "orm['subscriber.Subscriber']"}),
            'user_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'primary_key': 'True'})
        },
        'consumer.consumerhistoryevent': {
            'Meta': {'object_name': 'ConsumerHistoryEvent'},
            'consumer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'history'", 'to': "orm['consumer.Consumer']"}),
            'data': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'event_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'event_type': ('django.db.models.fields.CharField', [], {'default': "'0'", 'max_length': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.IPAddressField', [], {'default': "'0.0.0.0'", 'max_length': '15'})
        },
        'consumer.emailsubscription': {
            'Meta': {'object_name': 'EmailSubscription'},
            'email_subscription_name': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'consumer.salesrep': {
            'Meta': {'object_name': 'SalesRep'},
            'consumer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'salesreps'", 'to': "orm['consumer.Consumer']"}),
            'extension': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sites': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'reps'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['market.Site']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'})
        },
        'consumer.unemailablereason': {
            'Meta': {'object_name': 'UnEmailableReason'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '120'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'consumer.uniqueusertoken': {
            'Meta': {'object_name': 'UniqueUserToken'},
            'has_expiration': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'hashstamp': ('django.db.models.fields.CharField', [], {'max_length': '42', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lifetime': ('django.db.models.fields.IntegerField', [], {'default': '86400'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['consumer.Consumer']"})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
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
            'Meta': {'ordering': "('us_state', 'name')", 'object_name': 'USCity'},
            'coordinate': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'us_cities'", 'to': "orm['geolocation.Coordinate']"}),
            'geom': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '33'}),
            'us_county': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'us_cities'", 'to': "orm['geolocation.USCounty']"}),
            'us_state': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'us_cities'", 'to': "orm['geolocation.USState']"})
        },
        'geolocation.uscounty': {
            'Meta': {'ordering': "('us_state', 'name')", 'object_name': 'USCounty'},
            'geom': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'us_state': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'us_counties'", 'to': "orm['geolocation.USState']"})
        },
        'geolocation.usstate': {
            'Meta': {'ordering': "('name',)", 'object_name': 'USState'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '2'}),
            'geom': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '24'})
        },
        'geolocation.uszip': {
            'Meta': {'ordering': "('code',)", 'object_name': 'USZip'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '5'}),
            'coordinate': ('django.db.models.fields.related.ForeignKey', [], {'default': '1', 'related_name': "'us_zips'", 'null': 'True', 'blank': 'True', 'to': "orm['geolocation.Coordinate']"}),
            'geom': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'us_city': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'us_zips'", 'to': "orm['geolocation.USCity']"}),
            'us_county': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'us_zips'", 'to': "orm['geolocation.USCounty']"}),
            'us_state': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'us_zips'", 'to': "orm['geolocation.USState']"})
        },
        'market.site': {
            'Meta': {'ordering': "('id',)", 'object_name': 'Site'},
            'base_rate': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '6', 'decimal_places': '0'}),
            'coordinate': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'sites'", 'null': 'True', 'to': "orm['geolocation.Coordinate']"}),
            'default_state_province': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'site'", 'null': 'True', 'to': "orm['geolocation.USState']"}),
            'default_zip_postal': ('django.db.models.fields.CharField', [], {'max_length': '9', 'null': 'True', 'blank': 'True'}),
            'directory_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'envelope': ('django.contrib.gis.db.models.fields.GeometryField', [], {'null': 'True', 'blank': 'True'}),
            'geom': ('django.contrib.gis.db.models.fields.GeometryField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inactive_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'launch_date': ('django.db.models.fields.DateField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'market_cities': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'media_partner_allotment': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'phase': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'point': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True', 'blank': 'True'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'short_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '22'}),
            'us_city': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'sites'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['geolocation.USCity']"}),
            'us_county': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'sites'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['geolocation.USCounty']"}),
            'us_state': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'sites'", 'null': 'True', 'to': "orm['geolocation.USState']"}),
            'us_zip': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'sites'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['geolocation.USZip']"})
        },
        'subscriber.smssubscription': {
            'Meta': {'object_name': 'SMSSubscription'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sms_subscription_name': ('django.db.models.fields.CharField', [], {'max_length': '25'})
        },
        'subscriber.subscriber': {
            'Meta': {'object_name': 'Subscriber'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'default': '1', 'related_name': "'subscribers'", 'to': "orm['market.Site']"}),
            'sms_subscription': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'subscribers'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['subscriber.SMSSubscription']"}),
            'subscriber_create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'subscriber_modified_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'subscriber_zip_postal': ('django.db.models.fields.CharField', [], {'max_length': '9', 'null': 'True'})
        }
    }

    complete_apps = ['consumer']
