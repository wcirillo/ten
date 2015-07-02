# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'Historical.site'
        db.alter_column('ecommerce_historical', 'site_id', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, null=True, to=orm['market.Site']))


    def backwards(self, orm):
        
        # Changing field 'Historical.site'
        db.alter_column('ecommerce_historical', 'site_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['market.Site']))


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
            'category': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'businesses'", 'null': 'True', 'to': "orm['advertiser.Category']"}),
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
            'email_subscription': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'consumers'", 'blank': 'True', 'to': "orm['consumer.EmailSubscription']"}),
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
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'ecommerce.creditcard': {
            'Meta': {'object_name': 'CreditCard'},
            'business': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'credit_cards'", 'to': "orm['advertiser.Business']"}),
            'card_holder': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'cc_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'encrypted_number': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'exp_month': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'exp_year': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_storage_opt_in': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_4': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True'})
        },
        'ecommerce.historical': {
            'Meta': {'object_name': 'Historical'},
            'amount': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '2'}),
            'end_date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'historicals'", 'null': 'True', 'to': "orm['market.Site']"}),
            'start_date': ('django.db.models.fields.DateField', [], {})
        },
        'ecommerce.order': {
            'Meta': {'object_name': 'Order'},
            'amount_discounted': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '2'}),
            'billing_record': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'orders'", 'to': "orm['advertiser.BillingRecord']"}),
            'create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invoice': ('django.db.models.fields.CharField', [], {'max_length': '24', 'blank': 'True'}),
            'is_locked': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'default': "'V'", 'max_length': '2'}),
            'promoter_cut_amount': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '2'}),
            'promotion_code': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'orders'", 'null': 'True', 'to': "orm['ecommerce.PromotionCode']"}),
            'purchase_order': ('django.db.models.fields.CharField', [], {'max_length': '24', 'blank': 'True'}),
            'subtotal': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '2'}),
            'tax': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '2'}),
            'total': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '2'})
        },
        'ecommerce.orderitem': {
            'Meta': {'object_name': 'OrderItem'},
            'amount': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '2'}),
            'business': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'order_items'", 'to': "orm['advertiser.Business']"}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'end_datetime': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_taxable': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'item_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'order_items'", 'to': "orm['ecommerce.Order']"}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'order_items'", 'to': "orm['ecommerce.Product']"}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'order_items'", 'to': "orm['market.Site']"}),
            'start_datetime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2010, 7, 27, 11, 11, 57, 882784)'}),
            'units': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'})
        },
        'ecommerce.payment': {
            'Meta': {'object_name': 'Payment'},
            'amount': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '2'}),
            'create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'credit_card': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'payments'", 'null': 'True', 'to': "orm['ecommerce.CreditCard']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_locked': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_void': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'default': "'C'", 'max_length': '1'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'payments'", 'to': "orm['ecommerce.Order']"}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'p'", 'max_length': '1'})
        },
        'ecommerce.paymentresponse': {
            'Meta': {'object_name': 'PaymentResponse'},
            'avs_result_code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'batch': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'conversion_rate': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '4', 'blank': 'True'}),
            'converted_amount': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            'cvv2_result_code': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'error_description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_duplicate': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'payment': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'payment_responses'", 'unique': 'True', 'to': "orm['ecommerce.Payment']"}),
            'reference_number': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'ecommerce.product': {
            'Meta': {'object_name': 'Product'},
            'base_days': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'base_rate': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '2'}),
            'base_units': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '48'})
        },
        'ecommerce.promoter': {
            'Meta': {'object_name': 'Promoter'},
            'create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_approved': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_paid_traffic': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '48'}),
            'promoter_cut_percent': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '5', 'decimal_places': '2'}),
            'start_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.date(2010, 7, 27)'})
        },
        'ecommerce.promotion': {
            'Meta': {'object_name': 'Promotion'},
            'code_method': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'end_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.date(2011, 7, 27)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'monthly_usages_allowed': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'max_length': '3'}),
            'product': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'promotions'", 'to': "orm['ecommerce.Product']"}),
            'promo_amount': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'max_length': '3'}),
            'promo_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'promoter': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'promotions'", 'to': "orm['ecommerce.Promoter']"}),
            'start_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.date(2010, 7, 27)'}),
            'use_method': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'ecommerce.promotioncode': {
            'Meta': {'object_name': 'PromotionCode'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'promotion': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'promotion_codes'", 'to': "orm['ecommerce.Promotion']"}),
            'used_count': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'max_length': '8'})
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
            'coordinate': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'us_cities'", 'to': "orm['geolocation.Coordinate']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '33'}),
            'us_county': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'us_cities'", 'to': "orm['geolocation.USCounty']"}),
            'us_state': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'us_cities'", 'to': "orm['geolocation.USState']"})
        },
        'geolocation.uscounty': {
            'Meta': {'object_name': 'USCounty'},
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
            'Meta': {'object_name': 'USZip'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '5'}),
            'coordinate_id': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'us_city': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'us_zips'", 'to': "orm['geolocation.USCity']"}),
            'us_county': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'us_zips'", 'to': "orm['geolocation.USCounty']"}),
            'us_state': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'us_zips'", 'to': "orm['geolocation.USState']"})
        },
        'market.site': {
            'Meta': {'object_name': 'Site'},
            'base_rate': ('django.db.models.fields.DecimalField', [], {'default': '0', 'null': 'True', 'max_digits': '6', 'decimal_places': '0', 'blank': 'True'}),
            'broadcaster_allotment': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
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
            'us_city': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'sites'", 'null': 'True', 'to': "orm['geolocation.USCity']"}),
            'us_county': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'sites'", 'null': 'True', 'to': "orm['geolocation.USCounty']"}),
            'us_state': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'sites'", 'null': 'True', 'to': "orm['geolocation.USState']"}),
            'us_zip': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'sites'", 'null': 'True', 'to': "orm['geolocation.USZip']"})
        },
        'subscriber.carrier': {
            'Meta': {'object_name': 'Carrier'},
            'carrier': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'carrier_display_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_major_carrier': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'site': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'carriers'", 'to': "orm['market.Site']"}),
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
            'sms_subscription': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'subscribers'", 'blank': 'True', 'to': "orm['subscriber.SMSSubscription']"}),
            'subscriber_create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'subscriber_modified_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'subscriber_zip_postal': ('django.db.models.fields.CharField', [], {'max_length': '9', 'null': 'True'})
        }
    }

    complete_apps = ['ecommerce']
