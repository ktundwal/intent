# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'Intent'
        db.delete_table('query_intent')

        # Deleting model 'RunningState'
        db.delete_table('query_runningstate')

        # Deleting model 'Tweet'
        db.delete_table('query_tweet')

        # Adding model 'QueryResult'
        db.create_table('query_queryresult', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('result_of', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['query.Query'])),
            ('source', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('author', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('profile', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('language', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('source_id', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('cruxly_api_version', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('cruxly_rule_used', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('polarity', self.gf('django.db.models.fields.DecimalField')(default='0', max_digits=1, decimal_places=1)),
            ('subjectivity', self.gf('django.db.models.fields.DecimalField')(default='0', max_digits=1, decimal_places=1)),
            ('intent', self.gf('django.db.models.fields.IntegerField')(default=-1)),
            ('modality', self.gf('django.db.models.fields.DecimalField')(default='0', max_digits=1, decimal_places=1)),
        ))
        db.send_create_signal('query', ['QueryResult'])

        # Adding field 'Query.status'
        db.add_column('query_query', 'status',
                      self.gf('django.db.models.fields.IntegerField')(default=1),
                      keep_default=False)

    def backwards(self, orm):
        # Adding model 'Intent'
        db.create_table('query_intent', (
            ('intent', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('query', ['Intent'])

        # Adding model 'RunningState'
        db.create_table('query_runningstate', (
            ('query', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['query.Query'])),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('query', ['RunningState'])

        # Adding model 'Tweet'
        db.create_table('query_tweet', (
            ('profile', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('intent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['query.Intent'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('language', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('author', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('cruxly_rule_used', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('tweet_id', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('result_of', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['query.Query'])),
            ('cruxly_api_version', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal('query', ['Tweet'])

        # Deleting model 'QueryResult'
        db.delete_table('query_queryresult')

        # Deleting field 'Query.status'
        db.delete_column('query_query', 'status')

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
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'query.query': {
            'Meta': {'ordering': "['-created_on']", 'object_name': 'Query'},
            'count': ('django.db.models.fields.IntegerField', [], {'default': '100'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interval': ('django.db.models.fields.IntegerField', [], {'default': '1800'}),
            'last_run': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'latitude': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'radius': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'throttle': ('django.db.models.fields.FloatField', [], {'default': '0.5'})
        },
        'query.queryresult': {
            'Meta': {'ordering': "['-date']", 'object_name': 'QueryResult'},
            'author': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'cruxly_api_version': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'cruxly_rule_used': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'intent': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'modality': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '1', 'decimal_places': '1'}),
            'polarity': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '1', 'decimal_places': '1'}),
            'profile': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'result_of': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['query.Query']"}),
            'source': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'source_id': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'subjectivity': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '1', 'decimal_places': '1'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['query']