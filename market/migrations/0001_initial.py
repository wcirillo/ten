# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    depends_on = (
        ("geolocation", "0001_initial"),
    )

    def forwards(self, orm):
        
        # Adding model 'Site'
        db.create_table('market_site', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('domain', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('short_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=22)),
            ('region', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('directory_name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True, blank=True)),
            ('launch_date', self.gf('django.db.models.fields.DateField')(max_length=50, null=True, blank=True)),
            ('base_rate', self.gf('django.db.models.fields.DecimalField')(default=0, null=True, max_digits=6, decimal_places=0, blank=True)),
            ('default_zip_postal', self.gf('django.db.models.fields.CharField')(max_length=9, null=True, blank=True)),
            ('default_state_province', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='default_state_province', null=True, to=orm['geolocation.USState'])),
            ('market_cities', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('broadcaster_allotment', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0)),
            ('phase', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
            ('inactive_flag', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('us_state', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['geolocation.USState'], null=True, blank=True)),
        ))
        db.send_create_signal('market', ['Site'])

        # Adding M2M table for field us_county on 'Site'
        db.create_table('market_site_us_county', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('site', models.ForeignKey(orm['market.site'], null=False)),
            ('uscounty', models.ForeignKey(orm['geolocation.uscounty'], null=False))
        ))
        db.create_unique('market_site_us_county', ['site_id', 'uscounty_id'])

        # Adding M2M table for field us_city on 'Site'
        db.create_table('market_site_us_city', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('site', models.ForeignKey(orm['market.site'], null=False)),
            ('uscity', models.ForeignKey(orm['geolocation.uscity'], null=False))
        ))
        db.create_unique('market_site_us_city', ['site_id', 'uscity_id'])

        # Adding M2M table for field us_zip on 'Site'
        db.create_table('market_site_us_zip', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('site', models.ForeignKey(orm['market.site'], null=False)),
            ('uszip', models.ForeignKey(orm['geolocation.uszip'], null=False))
        ))
        db.create_unique('market_site_us_zip', ['site_id', 'uszip_id'])


    def backwards(self, orm):
        
        # Deleting model 'Site'
        db.delete_table('market_site')

        # Removing M2M table for field us_county on 'Site'
        db.delete_table('market_site_us_county')

        # Removing M2M table for field us_city on 'Site'
        db.delete_table('market_site_us_city')

        # Removing M2M table for field us_zip on 'Site'
        db.delete_table('market_site_us_zip')


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
        }
    }

    complete_apps = ['market']
