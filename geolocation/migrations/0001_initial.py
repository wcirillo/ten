# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Coordinate'
        db.create_table('geolocation_coordinate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('latitude', self.gf('django.db.models.fields.FloatField')()),
            ('longitude', self.gf('django.db.models.fields.FloatField')()),
            ('rad_lat', self.gf('django.db.models.fields.FloatField')()),
            ('rad_lon', self.gf('django.db.models.fields.FloatField')()),
            ('sin_rad_lat', self.gf('django.db.models.fields.FloatField')()),
            ('cos_rad_lat', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('geolocation', ['Coordinate'])

        # Adding model 'USState'
        db.create_table('geolocation_usstate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=24)),
            ('abbreviation', self.gf('django.db.models.fields.CharField')(unique=True, max_length=2)),
        ))
        db.send_create_signal('geolocation', ['USState'])

        # Adding model 'USCounty'
        db.create_table('geolocation_uscounty', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('us_state', self.gf('django.db.models.fields.related.ForeignKey')(related_name='us_counties', to=orm['geolocation.USState'])),
        ))
        db.send_create_signal('geolocation', ['USCounty'])

        # Adding model 'USCity'
        db.create_table('geolocation_uscity', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=33)),
            ('coordinate', self.gf('django.db.models.fields.related.ForeignKey')(related_name='us_cities', to=orm['geolocation.Coordinate'])),
            ('us_county', self.gf('django.db.models.fields.related.ForeignKey')(related_name='us_cities', to=orm['geolocation.USCounty'])),
            ('us_state', self.gf('django.db.models.fields.related.ForeignKey')(related_name='us_cities', to=orm['geolocation.USState'])),
        ))
        db.send_create_signal('geolocation', ['USCity'])

        # Adding model 'USZip'
        db.create_table('geolocation_uszip', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=5)),
            ('coordinate_id', self.gf('django.db.models.fields.IntegerField')()),
            ('us_city', self.gf('django.db.models.fields.related.ForeignKey')(related_name='us_zips', to=orm['geolocation.USCity'])),
            ('us_county', self.gf('django.db.models.fields.related.ForeignKey')(related_name='us_zips', to=orm['geolocation.USCounty'])),
            ('us_state', self.gf('django.db.models.fields.related.ForeignKey')(related_name='us_zips', to=orm['geolocation.USState'])),
        ))
        db.send_create_signal('geolocation', ['USZip'])


    def backwards(self, orm):
        
        # Deleting model 'Coordinate'
        db.delete_table('geolocation_coordinate')

        # Deleting model 'USState'
        db.delete_table('geolocation_usstate')

        # Deleting model 'USCounty'
        db.delete_table('geolocation_uscounty')

        # Deleting model 'USCity'
        db.delete_table('geolocation_uscity')

        # Deleting model 'USZip'
        db.delete_table('geolocation_uszip')


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
        }
    }

    complete_apps = ['geolocation']
