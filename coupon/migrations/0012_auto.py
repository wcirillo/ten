# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding index on 'Coupon', fields ['expiration_date']
        db.create_index('coupon_coupon', ['expiration_date'])

        # Adding index on 'Coupon', fields ['start_date']
        db.create_index('coupon_coupon', ['start_date'])


    def backwards(self, orm):
        
        # Removing index on 'Coupon', fields ['expiration_date']
        db.delete_index('coupon_coupon', ['expiration_date'])

        # Removing index on 'Coupon', fields ['start_date']
        db.delete_index('coupon_coupon', ['start_date'])


    models = {
        'advertiser.advertiser': {
            'Meta': {'object_name': 'Advertiser', '_ormbases': ['consumer.Consumer']},
            'advertiser_address1': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'advertiser_address2': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'advertiser_city': ('django.db.models.fields.CharField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'advertiser_create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'advertiser_modified_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'advertiser_phone': ('django.contrib.localflavor.us.models.PhoneNumberField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'advertiser_state_province': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'advertiser_zip_postal': ('django.db.models.fields.CharField', [], {'max_length': '9', 'null': 'True', 'blank': 'True'}),
            'approval_count': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'consumer_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['consumer.Consumer']", 'unique': 'True', 'primary_key': 'True'})
        },
        'advertiser.business': {
            'Meta': {'object_name': 'Business'},
            'advertiser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'businesses'", 'to': "orm['advertiser.Advertiser']"}),
            'business_create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'business_modified_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'business_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'business_zip_postal': ('django.db.models.fields.CharField', [], {'max_length': '9', 'null': 'True', 'blank': 'True'}),
            'category': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'businesses'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['advertiser.Category']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'short_business_name': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'slogan': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'})
        },
        'advertiser.category': {
            'Meta': {'object_name': 'Category'},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'advertiser.location': {
            'Meta': {'object_name': 'Location'},
            'business': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'locations'", 'to': "orm['advertiser.Business']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location_address1': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'location_address2': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'location_advertiser_label': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'location_area_code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'location_city': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'location_create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'location_description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'location_exchange': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'location_number': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'location_state_province': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'location_url': ('django.db.models.fields.URLField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'location_zip_postal': ('django.db.models.fields.CharField', [], {'max_length': '9', 'null': 'True', 'blank': 'True'})
        },
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
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'consumer.consumer': {
            'Meta': {'object_name': 'Consumer', '_ormbases': ['auth.User']},
            'consumer_create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'consumer_modified_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'consumer_zip_postal': ('django.db.models.fields.CharField', [], {'max_length': '9', 'null': 'True', 'blank': 'True'}),
            'email_hash': ('django.db.models.fields.CharField', [], {'max_length': '42', 'null': 'True', 'blank': 'True'}),
            'email_subscription': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'consumers'", 'blank': 'True', 'to': "orm['consumer.EmailSubscription']"}),
            'facebook_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'is_blacklisted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_bouncing_email': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_email_verified': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_perm_optout': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'default': '1', 'related_name': "'consumers'", 'to': "orm['market.Site']"}),
            'subscriber': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'subscribers'", 'unique': 'True', 'null': 'True', 'to': "orm['subscriber.Subscriber']"}),
            'user_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'primary_key': 'True'})
        },
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
        'coupon.action': {
            'Meta': {'object_name': 'Action'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'coupon.consumeraction': {
            'Meta': {'object_name': 'ConsumerAction'},
            'action': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'consumer_actions'", 'to': "orm['coupon.Action']"}),
            'consumer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'consumer_actions'", 'to': "orm['consumer.Consumer']"}),
            'coupon': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'consumer_actions'", 'to': "orm['coupon.Coupon']"}),
            'create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'coupon.coupon': {
            'Meta': {'object_name': 'Coupon'},
            'coupon_create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'coupon_modified_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'coupon_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'coupons'", 'to': "orm['coupon.CouponType']"}),
            'custom_restrictions': ('django.db.models.fields.TextField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'default_restrictions': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'coupons'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['coupon.DefaultRestrictions']"}),
            'expiration_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.date(2010, 12, 19)', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_approved': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_coupon_code_displayed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_redeemed_by_sms': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_valid_friday': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_valid_monday': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_valid_saturday': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_valid_sunday': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_valid_thursday': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_valid_tuesday': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_valid_wednesday': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'coupons'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['advertiser.Location']"}),
            'offer': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'coupons'", 'null': 'True', 'to': "orm['coupon.Offer']"}),
            'precise_url': ('django.db.models.fields.URLField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'redemption_method': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'coupons'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['coupon.RedemptionMethod']"}),
            'simple_code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'sms': ('django.db.models.fields.CharField', [], {'max_length': '61', 'null': 'True', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'})
        },
        'coupon.couponaction': {
            'Meta': {'unique_together': "(('action', 'coupon'),)", 'object_name': 'CouponAction'},
            'action': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'coupon_actions'", 'to': "orm['coupon.Action']"}),
            'count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'coupon': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'coupon_actions'", 'to': "orm['coupon.Coupon']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'coupon.couponcode': {
            'Meta': {'unique_together': "(('coupon', 'code'),)", 'object_name': 'CouponCode'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'coupon': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'coupon_codes'", 'to': "orm['coupon.Coupon']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'used_count': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'max_length': '8'})
        },
        'coupon.coupontype': {
            'Meta': {'object_name': 'CouponType'},
            'coupon_type_name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'coupon.defaultrestrictions': {
            'Meta': {'object_name': 'DefaultRestrictions'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restriction': ('django.db.models.fields.CharField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'sort_order': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '1'})
        },
        'coupon.flyer': {
            'Meta': {'object_name': 'Flyer'},
            'coupon': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'flyers'", 'symmetrical': 'False', 'through': "orm['coupon.FlyerCoupon']", 'to': "orm['coupon.Coupon']"}),
            'create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_approved': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_mini': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'num_recipients': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'send_status': ('django.db.models.fields.CharField', [], {'default': '0', 'max_length': '1'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'flyers'", 'to': "orm['market.Site']"})
        },
        'coupon.flyercoupon': {
            'Meta': {'unique_together': "(('flyer', 'rank'),)", 'object_name': 'FlyerCoupon'},
            'coupon': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'flyer_coupons'", 'to': "orm['coupon.Coupon']"}),
            'flyer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'flyer_coupons'", 'to': "orm['coupon.Flyer']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rank': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'max_length': '2'})
        },
        'coupon.offer': {
            'Meta': {'object_name': 'Offer'},
            'business': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'offers'", 'null': 'True', 'to': "orm['advertiser.Business']"}),
            'create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'headline': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'qualifier': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'})
        },
        'coupon.redemptionmethod': {
            'Meta': {'object_name': 'RedemptionMethod'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'redemption_method_name': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'})
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
            'Meta': {'object_name': 'USState'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '24'})
        },
        'geolocation.uszip': {
            'Meta': {'ordering': "('code',)", 'object_name': 'USZip'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '5'}),
            'coordinate': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'us_zips'", 'to': "orm['geolocation.Coordinate']"}),
            'geom': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'us_city': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'us_zips'", 'to': "orm['geolocation.USCity']"}),
            'us_county': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'us_zips'", 'to': "orm['geolocation.USCounty']"}),
            'us_state': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'us_zips'", 'to': "orm['geolocation.USState']"})
        },
        'market.site': {
            'Meta': {'ordering': "('id',)", 'object_name': 'Site'},
            'base_rate': ('django.db.models.fields.DecimalField', [], {'default': '0', 'null': 'True', 'max_digits': '6', 'decimal_places': '0', 'blank': 'True'}),
            'broadcaster_allotment': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'coordinate': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'sites'", 'null': 'True', 'to': "orm['geolocation.Coordinate']"}),
            'default_state_province': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'site'", 'null': 'True', 'to': "orm['geolocation.USState']"}),
            'default_zip_postal': ('django.db.models.fields.CharField', [], {'max_length': '9', 'null': 'True', 'blank': 'True'}),
            'directory_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'facebook_key': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'facebook_secret': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inactive_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'launch_date': ('django.db.models.fields.DateField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'market_cities': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'phase': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'short_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '22'}),
            'twitter_name': ('django.db.models.fields.CharField', [], {'max_length': '15', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'us_city': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'sites'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['geolocation.USCity']"}),
            'us_county': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'sites'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['geolocation.USCounty']"}),
            'us_state': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'sites'", 'null': 'True', 'to': "orm['geolocation.USState']"}),
            'us_zip': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'sites'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['geolocation.USZip']"})
        },
        'subscriber.carrier': {
            'Meta': {'ordering': "('-is_major_carrier', 'carrier_display_name')", 'object_name': 'Carrier'},
            'carrier': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'carrier_display_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_major_carrier': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'site': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'carriers'", 'symmetrical': 'False', 'to': "orm['market.Site']"}),
            'user_name': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'})
        },
        'subscriber.mobilephone': {
            'Meta': {'object_name': 'MobilePhone'},
            'carrier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'mobile_phones'", 'to': "orm['subscriber.Carrier']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mobile_phone_number': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        },
        'subscriber.smssubscription': {
            'Meta': {'object_name': 'SMSSubscription'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sms_subscription_name': ('django.db.models.fields.CharField', [], {'max_length': '25'})
        },
        'subscriber.subscriber': {
            'Meta': {'object_name': 'Subscriber'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mobile_phone': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'subscribers'", 'blank': 'True', 'to': "orm['subscriber.MobilePhone']"}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'default': '1', 'related_name': "'subscribers'", 'to': "orm['market.Site']"}),
            'sms_subscription': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'subscribers'", 'blank': 'True', 'to': "orm['subscriber.SMSSubscription']"}),
            'subscriber_create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'subscriber_modified_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'subscriber_zip_postal': ('django.db.models.fields.CharField', [], {'max_length': '9', 'null': 'True'})
        }
    }

    complete_apps = ['coupon']
