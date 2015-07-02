# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'DefaultRestrictions'
        db.create_table('coupon_defaultrestrictions', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('restriction', self.gf('django.db.models.fields.CharField')(max_length=75, null=True, blank=True)),
            ('sort_order', self.gf('django.db.models.fields.CharField')(unique=True, max_length=1)),
        ))
        db.send_create_signal('coupon', ['DefaultRestrictions'])

        # Adding model 'RedemptionMethod'
        db.create_table('coupon_redemptionmethod', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('redemption_method_name', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
        ))
        db.send_create_signal('coupon', ['RedemptionMethod'])

        # Adding model 'Offer'
        db.create_table('coupon_offer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('business', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['advertiser.Business'], null=True, blank=True)),
            ('headline', self.gf('django.db.models.fields.CharField')(max_length=25, null=True, blank=True)),
            ('qualifier', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('create_datetime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('coupon', ['Offer'])

        # Adding model 'CouponType'
        db.create_table('coupon_coupontype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('coupon_type_name', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal('coupon', ['CouponType'])

        # Adding model 'Coupon'
        db.create_table('coupon_coupon', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('offer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['coupon.Offer'], null=True, blank=True)),
            ('coupon_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['coupon.CouponType'], null=True, blank=True)),
            ('is_valid_monday', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('is_valid_tuesday', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('is_valid_wednesday', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('is_valid_thursday', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('is_valid_friday', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('is_valid_saturday', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('is_valid_sunday', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('start_date', self.gf('django.db.models.fields.DateField')(default=datetime.date.today)),
            ('expiration_date', self.gf('django.db.models.fields.DateField')(default=datetime.date(2010, 8, 18))),
            ('custom_restrictions', self.gf('django.db.models.fields.TextField')(max_length=400, null=True, blank=True)),
            ('simple_code', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('is_redeemed_by_sms', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('is_coupon_code_displayed', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('is_approved', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('precise_url', self.gf('django.db.models.fields.URLField')(max_length=255, null=True, blank=True)),
            ('coupon_create_datetime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('coupon_modified_datetime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('coupon', ['Coupon'])

        # Adding M2M table for field redemption_method on 'Coupon'
        db.create_table('coupon_coupon_redemption_method', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('coupon', models.ForeignKey(orm['coupon.coupon'], null=False)),
            ('redemptionmethod', models.ForeignKey(orm['coupon.redemptionmethod'], null=False))
        ))
        db.create_unique('coupon_coupon_redemption_method', ['coupon_id', 'redemptionmethod_id'])

        # Adding M2M table for field location on 'Coupon'
        db.create_table('coupon_coupon_location', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('coupon', models.ForeignKey(orm['coupon.coupon'], null=False)),
            ('location', models.ForeignKey(orm['advertiser.location'], null=False))
        ))
        db.create_unique('coupon_coupon_location', ['coupon_id', 'location_id'])

        # Adding M2M table for field default_restrictions on 'Coupon'
        db.create_table('coupon_coupon_default_restrictions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('coupon', models.ForeignKey(orm['coupon.coupon'], null=False)),
            ('defaultrestrictions', models.ForeignKey(orm['coupon.defaultrestrictions'], null=False))
        ))
        db.create_unique('coupon_coupon_default_restrictions', ['coupon_id', 'defaultrestrictions_id'])

        # Adding model 'CouponCode'
        db.create_table('coupon_couponcode', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('coupon', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['coupon.Coupon'])),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('used_count', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, max_length=8)),
        ))
        db.send_create_signal('coupon', ['CouponCode'])

        # Adding unique constraint on 'CouponCode', fields ['coupon', 'code']
        db.create_unique('coupon_couponcode', ['coupon_id', 'code'])


    def backwards(self, orm):
        
        # Deleting model 'DefaultRestrictions'
        db.delete_table('coupon_defaultrestrictions')

        # Deleting model 'RedemptionMethod'
        db.delete_table('coupon_redemptionmethod')

        # Deleting model 'Offer'
        db.delete_table('coupon_offer')

        # Deleting model 'CouponType'
        db.delete_table('coupon_coupontype')

        # Deleting model 'Coupon'
        db.delete_table('coupon_coupon')

        # Removing M2M table for field redemption_method on 'Coupon'
        db.delete_table('coupon_coupon_redemption_method')

        # Removing M2M table for field location on 'Coupon'
        db.delete_table('coupon_coupon_location')

        # Removing M2M table for field default_restrictions on 'Coupon'
        db.delete_table('coupon_coupon_default_restrictions')

        # Deleting model 'CouponCode'
        db.delete_table('coupon_couponcode')

        # Removing unique constraint on 'CouponCode', fields ['coupon', 'code']
        db.delete_unique('coupon_couponcode', ['coupon_id', 'code'])


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
            'advertiser': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['advertiser.Advertiser']"}),
            'business_create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'business_modified_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'business_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'category': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['advertiser.Category']", 'null': 'True', 'blank': 'True'}),
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
            'business': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['advertiser.Business']"}),
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
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'consumer.consumer': {
            'Meta': {'object_name': 'Consumer', '_ormbases': ['auth.User']},
            'consumer_create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'consumer_modified_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'consumer_zip_postal': ('django.db.models.fields.CharField', [], {'max_length': '9', 'null': 'True', 'blank': 'True'}),
            'email_subscription': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['consumer.EmailSubscription']", 'blank': 'True'}),
            'is_email_verified': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'default': '1', 'to': "orm['market.Site']"}),
            'subscriber': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['subscriber.Subscriber']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'user_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'primary_key': 'True'})
        },
        'consumer.emailsubscription': {
            'Meta': {'object_name': 'EmailSubscription'},
            'email_subscription_name': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'coupon.coupon': {
            'Meta': {'object_name': 'Coupon'},
            'coupon_create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'coupon_modified_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'coupon_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['coupon.CouponType']", 'null': 'True', 'blank': 'True'}),
            'custom_restrictions': ('django.db.models.fields.TextField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'default_restrictions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['coupon.DefaultRestrictions']", 'null': 'True', 'blank': 'True'}),
            'expiration_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.date(2010, 8, 18)'}),
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
            'location': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['advertiser.Location']", 'null': 'True', 'blank': 'True'}),
            'offer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['coupon.Offer']", 'null': 'True', 'blank': 'True'}),
            'precise_url': ('django.db.models.fields.URLField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'redemption_method': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['coupon.RedemptionMethod']", 'null': 'True', 'blank': 'True'}),
            'simple_code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'})
        },
        'coupon.couponcode': {
            'Meta': {'unique_together': "(('coupon', 'code'),)", 'object_name': 'CouponCode'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'coupon': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['coupon.Coupon']"}),
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
        'coupon.offer': {
            'Meta': {'object_name': 'Offer'},
            'business': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['advertiser.Business']", 'null': 'True', 'blank': 'True'}),
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
        },
        'subscriber.smssubscription': {
            'Meta': {'object_name': 'SMSSubscription'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sms_subscription_name': ('django.db.models.fields.CharField', [], {'max_length': '25'})
        },
        'subscriber.subscriber': {
            'Meta': {'object_name': 'Subscriber'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mobile_phone': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['subscriber.MobilePhone']", 'blank': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'default': '1', 'to': "orm['market.Site']"}),
            'sms_subscription': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['subscriber.SMSSubscription']", 'blank': 'True'}),
            'subscriber_create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'subscriber_modified_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'subscriber_zip_postal': ('django.db.models.fields.CharField', [], {'max_length': '9', 'null': 'True'})
        }
    }

    complete_apps = ['coupon']
