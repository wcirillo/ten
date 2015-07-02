# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Product'
        db.create_table('ecommerce_product', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=48)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('base_rate', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=8, decimal_places=2)),
            ('base_units', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=8, decimal_places=0)),
            ('base_days', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0)),
        ))
        db.send_create_signal('ecommerce', ['Product'])

        # Adding model 'Promoter'
        db.create_table('ecommerce_promoter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=48)),
            ('is_approved', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('start_date', self.gf('django.db.models.fields.DateField')(default=datetime.date(2010, 5, 20))),
            ('end_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('promoter_cut_percent', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=5, decimal_places=2)),
            ('create_datetime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('ecommerce', ['Promoter'])

        # Adding model 'Promotion'
        db.create_table('ecommerce_promotion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('promoter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ecommerce.Promoter'])),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('promo_type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('promo_amount', self.gf('django.db.models.fields.SmallIntegerField')(default=0, max_length=3)),
            ('use_method', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('monthly_usages_allowed', self.gf('django.db.models.fields.SmallIntegerField')(default=0, max_length=3)),
            ('code_method', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('start_date', self.gf('django.db.models.fields.DateField')(default=datetime.date(2010, 5, 20))),
            ('end_date', self.gf('django.db.models.fields.DateField')(default=datetime.date(2011, 5, 20))),
            ('create_datetime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('ecommerce', ['Promotion'])

        # Adding M2M table for field product on 'Promotion'
        db.create_table('ecommerce_promotion_product', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('promotion', models.ForeignKey(orm['ecommerce.promotion'], null=False)),
            ('product', models.ForeignKey(orm['ecommerce.product'], null=False))
        ))
        db.create_unique('ecommerce_promotion_product', ['promotion_id', 'product_id'])

        # Adding model 'PromotionCode'
        db.create_table('ecommerce_promotioncode', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('promotion', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ecommerce.Promotion'])),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('used_count', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, max_length=8)),
        ))
        db.send_create_signal('ecommerce', ['PromotionCode'])

        # Adding model 'Order'
        db.create_table('ecommerce_order', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('billing_record', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['advertiser.BillingRecord'])),
            ('method', self.gf('django.db.models.fields.CharField')(default='V', max_length=2)),
            ('promotion_code', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ecommerce.PromotionCode'], null=True, blank=True)),
            ('subtotal', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=8, decimal_places=2)),
            ('amount_discounted', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=8, decimal_places=2)),
            ('tax', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=8, decimal_places=2)),
            ('total', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=8, decimal_places=2)),
            ('promoter_cut_amount', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=8, decimal_places=2)),
            ('invoice', self.gf('django.db.models.fields.CharField')(max_length=24, blank=True)),
            ('purchase_order', self.gf('django.db.models.fields.CharField')(max_length=24, blank=True)),
            ('create_datetime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('is_locked', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('ecommerce', ['Order'])

        # Adding model 'OrderItem'
        db.create_table('ecommerce_orderitem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('site', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['market.Site'])),
            ('order', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ecommerce.Order'])),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ecommerce.Product'])),
            ('item_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('business', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['advertiser.Business'])),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=48)),
            ('units', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
            ('amount', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=8, decimal_places=2)),
            ('is_taxable', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('start_datetime', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2010, 5, 20, 15, 17, 55, 480419))),
            ('end_datetime', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('ecommerce', ['OrderItem'])

        # Adding model 'CreditCard'
        db.create_table('ecommerce_creditcard', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('cc_type', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('encrypted_number', self.gf('django.db.models.fields.CharField')(max_length=128, null=True)),
            ('business', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['advertiser.Business'])),
            ('is_storage_opt_in', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('exp_month', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('exp_year', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('card_holder', self.gf('django.db.models.fields.CharField')(max_length=64, null=True)),
            ('last_4', self.gf('django.db.models.fields.CharField')(max_length=4, null=True)),
        ))
        db.send_create_signal('ecommerce', ['CreditCard'])

        # Adding model 'Payment'
        db.create_table('ecommerce_payment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('order', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ecommerce.Order'])),
            ('credit_card', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ecommerce.CreditCard'], null=True)),
            ('amount', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=8, decimal_places=2)),
            ('method', self.gf('django.db.models.fields.CharField')(default='C', max_length=1)),
            ('status', self.gf('django.db.models.fields.CharField')(default='p', max_length=1)),
            ('create_datetime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('is_void', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('is_locked', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('ecommerce', ['Payment'])

        # Adding model 'PaymentResponse'
        db.create_table('ecommerce_paymentresponse', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('payment', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['ecommerce.Payment'], unique=True)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('reference_number', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('batch', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('error_description', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('avs_result_code', self.gf('django.db.models.fields.CharField')(max_length=3, blank=True)),
            ('cvv2_result_code', self.gf('django.db.models.fields.CharField')(max_length=1, blank=True)),
            ('converted_amount', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=6, decimal_places=2, blank=True)),
            ('conversion_rate', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=6, decimal_places=4, blank=True)),
            ('is_duplicate', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('ecommerce', ['PaymentResponse'])


    def backwards(self, orm):
        
        # Deleting model 'Product'
        db.delete_table('ecommerce_product')

        # Deleting model 'Promoter'
        db.delete_table('ecommerce_promoter')

        # Deleting model 'Promotion'
        db.delete_table('ecommerce_promotion')

        # Removing M2M table for field product on 'Promotion'
        db.delete_table('ecommerce_promotion_product')

        # Deleting model 'PromotionCode'
        db.delete_table('ecommerce_promotioncode')

        # Deleting model 'Order'
        db.delete_table('ecommerce_order')

        # Deleting model 'OrderItem'
        db.delete_table('ecommerce_orderitem')

        # Deleting model 'CreditCard'
        db.delete_table('ecommerce_creditcard')

        # Deleting model 'Payment'
        db.delete_table('ecommerce_payment')

        # Deleting model 'PaymentResponse'
        db.delete_table('ecommerce_paymentresponse')


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
            'billing_address1': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'billing_address2': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'billing_city': ('django.db.models.fields.CharField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'billing_state_province': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'billing_zip_postal': ('django.db.models.fields.CharField', [], {'max_length': '9'}),
            'business': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['advertiser.Business']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
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
        'ecommerce.creditcard': {
            'Meta': {'object_name': 'CreditCard'},
            'business': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['advertiser.Business']"}),
            'card_holder': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'cc_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'encrypted_number': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'exp_month': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'exp_year': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_storage_opt_in': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_4': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True'})
        },
        'ecommerce.order': {
            'Meta': {'object_name': 'Order'},
            'amount_discounted': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '2'}),
            'billing_record': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['advertiser.BillingRecord']"}),
            'create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invoice': ('django.db.models.fields.CharField', [], {'max_length': '24', 'blank': 'True'}),
            'is_locked': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'default': "'V'", 'max_length': '2'}),
            'promoter_cut_amount': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '2'}),
            'promotion_code': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ecommerce.PromotionCode']", 'null': 'True', 'blank': 'True'}),
            'purchase_order': ('django.db.models.fields.CharField', [], {'max_length': '24', 'blank': 'True'}),
            'subtotal': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '2'}),
            'tax': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '2'}),
            'total': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '2'})
        },
        'ecommerce.orderitem': {
            'Meta': {'object_name': 'OrderItem'},
            'amount': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '2'}),
            'business': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['advertiser.Business']"}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '48'}),
            'end_datetime': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_taxable': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'item_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ecommerce.Order']"}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ecommerce.Product']"}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['market.Site']"}),
            'start_datetime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2010, 5, 20, 15, 17, 55, 480419)'}),
            'units': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'})
        },
        'ecommerce.payment': {
            'Meta': {'object_name': 'Payment'},
            'amount': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '2'}),
            'create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'credit_card': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ecommerce.CreditCard']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_locked': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_void': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'default': "'C'", 'max_length': '1'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ecommerce.Order']"}),
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
            'payment': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['ecommerce.Payment']", 'unique': 'True'}),
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
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '48'}),
            'promoter_cut_percent': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '5', 'decimal_places': '2'}),
            'start_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.date(2010, 5, 20)'})
        },
        'ecommerce.promotion': {
            'Meta': {'object_name': 'Promotion'},
            'code_method': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'end_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.date(2011, 5, 20)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'monthly_usages_allowed': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'max_length': '3'}),
            'product': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['ecommerce.Product']"}),
            'promo_amount': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'max_length': '3'}),
            'promo_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'promoter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ecommerce.Promoter']"}),
            'start_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.date(2010, 5, 20)'}),
            'use_method': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'ecommerce.promotioncode': {
            'Meta': {'object_name': 'PromotionCode'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'promotion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ecommerce.Promotion']"}),
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

    complete_apps = ['ecommerce']
