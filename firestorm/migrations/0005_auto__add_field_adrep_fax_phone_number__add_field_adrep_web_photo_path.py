# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'AdRep.fax_phone_number'
        db.add_column('firestorm_adrep', 'fax_phone_number', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True), keep_default=False)

        # Adding field 'AdRep.web_photo_path'
        db.add_column('firestorm_adrep', 'web_photo_path', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True), keep_default=False)

        # Adding field 'AdRep.mailing_address1'
        db.add_column('firestorm_adrep', 'mailing_address1', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True), keep_default=False)

        # Adding field 'AdRep.mailing_address2'
        db.add_column('firestorm_adrep', 'mailing_address2', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True), keep_default=False)

        # Adding field 'AdRep.mailing_city'
        db.add_column('firestorm_adrep', 'mailing_city', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True), keep_default=False)

        # Adding field 'AdRep.mailing_state_province'
        db.add_column('firestorm_adrep', 'mailing_state_province', self.gf('django.db.models.fields.CharField')(max_length=2, null=True, blank=True), keep_default=False)

        # Adding field 'AdRep.mailing_zip_postal'
        db.add_column('firestorm_adrep', 'mailing_zip_postal', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=9, null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'AdRep.fax_phone_number'
        db.delete_column('firestorm_adrep', 'fax_phone_number')

        # Deleting field 'AdRep.web_photo_path'
        db.delete_column('firestorm_adrep', 'web_photo_path')

        # Deleting field 'AdRep.mailing_address1'
        db.delete_column('firestorm_adrep', 'mailing_address1')

        # Deleting field 'AdRep.mailing_address2'
        db.delete_column('firestorm_adrep', 'mailing_address2')

        # Deleting field 'AdRep.mailing_city'
        db.delete_column('firestorm_adrep', 'mailing_city')

        # Deleting field 'AdRep.mailing_state_province'
        db.delete_column('firestorm_adrep', 'mailing_state_province')

        # Deleting field 'AdRep.mailing_zip_postal'
        db.delete_column('firestorm_adrep', 'mailing_zip_postal')


    models = {
        'advertiser.advertiser': {
            'Meta': {'object_name': 'Advertiser', '_ormbases': ['consumer.Consumer']},
            'advertiser_address1': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'advertiser_address2': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'advertiser_area_code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'advertiser_city': ('django.db.models.fields.CharField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'advertiser_create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'advertiser_exchange': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'advertiser_modified_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'advertiser_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'advertiser_number': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'advertiser_state_province': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'advertiser_zip_postal': ('django.db.models.fields.CharField', [], {'max_length': '9', 'null': 'True', 'blank': 'True'}),
            'approval_count': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'consumer_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['consumer.Consumer']", 'unique': 'True', 'primary_key': 'True'})
        },
        'advertiser.billingrecord': {
            'Meta': {'object_name': 'BillingRecord'},
            'alt_email': ('django.db.models.fields.EmailField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'alt_first_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'alt_last_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'billing_address1': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'billing_address2': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'billing_city': ('django.db.models.fields.CharField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'billing_state_province': ('django.db.models.fields.CharField', [], {'max_length': '2', 'blank': 'True'}),
            'billing_zip_postal': ('django.db.models.fields.CharField', [], {'max_length': '9', 'blank': 'True'}),
            'business': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'billing_records'", 'to': "orm['advertiser.Business']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'advertiser.business': {
            'Meta': {'object_name': 'Business'},
            'advertiser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'businesses'", 'to': "orm['advertiser.Advertiser']"}),
            'business_create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'business_modified_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'business_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'business_zip_postal': ('django.db.models.fields.CharField', [], {'max_length': '9', 'null': 'True', 'blank': 'True'}),
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'businesses'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['category.Category']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'short_business_name': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'show_map': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'show_web_snap': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slogan': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'web_snap_path': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'web_url': ('django.db.models.fields.URLField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'advertiser.location': {
            'Meta': {'object_name': 'Location'},
            'business': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'locations'", 'to': "orm['advertiser.Business']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location_address1': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'location_address2': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'location_area_code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'location_city': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'location_create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'location_description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'location_exchange': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'location_number': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'location_state_province': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'location_url': ('django.db.models.fields.URLField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'location_zip_postal': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '9', 'null': 'True', 'blank': 'True'})
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
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'category.category': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Category'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
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
        'consumer.emailsubscription': {
            'Meta': {'object_name': 'EmailSubscription'},
            'email_subscription_name': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'consumer.unemailablereason': {
            'Meta': {'object_name': 'UnEmailableReason'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '120'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'coupon.coupon': {
            'Meta': {'object_name': 'Coupon'},
            'coupon_create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'coupon_modified_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'coupon_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'coupons'", 'to': "orm['coupon.CouponType']"}),
            'custom_restrictions': ('django.db.models.fields.TextField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'default_restrictions': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'coupons'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['coupon.DefaultRestrictions']"}),
            'expiration_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.date(2011, 11, 6)', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_coupon_code_displayed': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_redeemed_by_sms': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_valid_friday': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_valid_monday': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_valid_saturday': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_valid_sunday': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_valid_thursday': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_valid_tuesday': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_valid_wednesday': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'location': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'coupons'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['advertiser.Location']"}),
            'offer': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'coupons'", 'null': 'True', 'to': "orm['coupon.Offer']"}),
            'precise_url': ('django.db.models.fields.URLField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'redemption_method': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'coupons'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['coupon.RedemptionMethod']"}),
            'simple_code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'sms': ('django.db.models.fields.CharField', [], {'max_length': '61', 'null': 'True', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'})
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
            'is_approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_mini': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'num_recipients': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'send_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today', 'db_index': 'True'}),
            'send_datetime': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'send_status': ('django.db.models.fields.CharField', [], {'default': "'0'", 'max_length': '1'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'flyers'", 'to': "orm['market.Site']"})
        },
        'coupon.flyercoupon': {
            'Meta': {'unique_together': "(('flyer', 'rank'), ('flyer', 'coupon'))", 'object_name': 'FlyerCoupon'},
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
        'ecommerce.order': {
            'Meta': {'object_name': 'Order'},
            'amount_discounted': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '2'}),
            'billing_record': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'orders'", 'to': "orm['advertiser.BillingRecord']"}),
            'create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invoice': ('django.db.models.fields.CharField', [], {'max_length': '24', 'blank': 'True'}),
            'is_locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'method': ('django.db.models.fields.CharField', [], {'default': "'V'", 'max_length': '2'}),
            'promoter_cut_amount': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '2'}),
            'promotion_code': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'orders'", 'null': 'True', 'to': "orm['ecommerce.PromotionCode']"}),
            'purchase_order': ('django.db.models.fields.CharField', [], {'max_length': '24', 'blank': 'True'}),
            'subtotal': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '2'}),
            'tax': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '2'}),
            'total': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '2'})
        },
        'ecommerce.product': {
            'Meta': {'ordering': "('id',)", 'object_name': 'Product'},
            'base_days': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'base_rate': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '2'}),
            'base_units': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '0'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '48'})
        },
        'ecommerce.promoter': {
            'Meta': {'object_name': 'Promoter'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'guid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_paid_traffic': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '48', 'db_index': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'promoter_cut_percent': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '5', 'decimal_places': '2'}),
            'start_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'})
        },
        'ecommerce.promotion': {
            'Meta': {'object_name': 'Promotion'},
            'code_method': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'end_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.date(2012, 8, 7)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'monthly_usages_allowed': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'max_length': '3'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '48', 'db_index': 'True'}),
            'product': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'promotions'", 'symmetrical': 'False', 'to': "orm['ecommerce.Product']"}),
            'promo_amount': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'max_length': '3'}),
            'promo_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'promoter': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'promotions'", 'to': "orm['ecommerce.Promoter']"}),
            'start_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'}),
            'use_method': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'ecommerce.promotioncode': {
            'Meta': {'object_name': 'PromotionCode'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'promotion': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'promotion_codes'", 'to': "orm['ecommerce.Promotion']"}),
            'used_count': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'max_length': '8'})
        },
        'firestorm.adrep': {
            'Meta': {'object_name': 'AdRep', '_ormbases': ['consumer.Consumer']},
            'company': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'consumer_points': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'consumer_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['consumer.Consumer']", 'unique': 'True', 'primary_key': 'True'}),
            'fax_phone_number': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'firestorm_id': ('django.db.models.fields.PositiveIntegerField', [], {'unique': 'True'}),
            'home_phone_number': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'mailing_address1': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'mailing_address2': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'mailing_city': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'mailing_state_province': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'mailing_zip_postal': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '9', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '25'}),
            'web_photo_path': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'work_phone_number': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        'firestorm.adrepadvertiser': {
            'Meta': {'object_name': 'AdRepAdvertiser'},
            'ad_rep': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ad_rep_advertisers'", 'to': "orm['firestorm.AdRep']"}),
            'advertiser': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'ad_rep_advertiser'", 'unique': 'True', 'to': "orm['advertiser.Advertiser']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'firestorm.adrepconsumer': {
            'Meta': {'object_name': 'AdRepConsumer'},
            'ad_rep': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ad_rep_consumers'", 'to': "orm['firestorm.AdRep']"}),
            'consumer': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'ad_rep_consumer'", 'unique': 'True', 'to': "orm['consumer.Consumer']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'firestorm.adreporder': {
            'Meta': {'object_name': 'AdRepOrder'},
            'ad_rep': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ad_rep_orders'", 'to': "orm['firestorm.AdRep']"}),
            'firestorm_order_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'ad_rep_order'", 'unique': 'True', 'to': "orm['ecommerce.Order']"})
        },
        'firestorm.adrepwebgreeting': {
            'Meta': {'object_name': 'AdRepWebGreeting'},
            'ad_rep': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['firestorm.AdRep']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'web_greeting': ('django.db.models.fields.TextField', [], {'max_length': '2500', 'null': 'True', 'blank': 'True'})
        },
        'firestorm.bonuspoolflyer': {
            'Meta': {'object_name': 'BonusPoolFlyer'},
            'calculate_status': ('django.db.models.fields.CharField', [], {'default': "'0'", 'max_length': '1'}),
            'flyer': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['coupon.Flyer']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
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

    complete_apps = ['firestorm']
