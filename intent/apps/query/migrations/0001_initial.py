# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Rule'
        db.create_table('query_rule', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('grammar', self.gf('django.db.models.fields.IntegerField')()),
            ('grammar_version', self.gf('django.db.models.fields.DecimalField')(max_digits=2, decimal_places=1)),
            ('rule', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('confidence', self.gf('django.db.models.fields.DecimalField')(default=1.0, max_digits=2, decimal_places=1)),
        ))
        db.send_create_signal('query', ['Rule'])

        # Adding model 'Query'
        db.create_table('query_query', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('query', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('last_run', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('interval', self.gf('django.db.models.fields.IntegerField')(default=1800)),
            ('count', self.gf('django.db.models.fields.IntegerField')(default=100)),
            ('throttle', self.gf('django.db.models.fields.FloatField')(default=0.5)),
            ('latitude', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('longitude', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('radius', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('num_times_run', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('query_exception', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
        ))
        db.send_create_signal('query', ['Query'])

        # Adding model 'Author'
        db.create_table('query_author', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('twitter_handle', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=40)),
        ))
        db.send_create_signal('query', ['Author'])

        # Adding model 'Document'
        db.create_table('query_document', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('result_of', self.gf('django.db.models.fields.related.ForeignKey')(related_name='results', blank=True, to=orm['query.Query'])),
            ('source', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='documents', to=orm['query.Author'])),
            ('source_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=40)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('analyzed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('want_rule', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='wants', null=True, to=orm['query.Rule'])),
            ('question_rule', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='questions', null=True, to=orm['query.Rule'])),
            ('promise_rule', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='promises', null=True, to=orm['query.Rule'])),
            ('dislike_rule', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='dislikes', null=True, to=orm['query.Rule'])),
            ('polarity', self.gf('django.db.models.fields.DecimalField')(default='0', max_digits=2, decimal_places=1)),
            ('subjectivity', self.gf('django.db.models.fields.DecimalField')(default='0', max_digits=2, decimal_places=1)),
            ('intent', self.gf('django.db.models.fields.IntegerField')(default=-1)),
            ('modality', self.gf('django.db.models.fields.DecimalField')(default='0', max_digits=2, decimal_places=1)),
        ))
        db.send_create_signal('query', ['Document'])

    def backwards(self, orm):
        # Deleting model 'Rule'
        db.delete_table('query_rule')

        # Deleting model 'Query'
        db.delete_table('query_query')

        # Deleting model 'Author'
        db.delete_table('query_author')

        # Deleting model 'Document'
        db.delete_table('query_document')

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
        'query.author': {
            'Meta': {'object_name': 'Author'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'twitter_handle': ('django.db.models.fields.CharField', [], {'max_length': '40'})
        },
        'query.document': {
            'Meta': {'ordering': "['-date']", 'object_name': 'Document'},
            'analyzed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'documents'", 'to': "orm['query.Author']"}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dislike_rule': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'dislikes'", 'null': 'True', 'to': "orm['query.Rule']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'intent': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'modality': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '2', 'decimal_places': '1'}),
            'polarity': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '2', 'decimal_places': '1'}),
            'promise_rule': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'promises'", 'null': 'True', 'to': "orm['query.Rule']"}),
            'question_rule': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'questions'", 'null': 'True', 'to': "orm['query.Rule']"}),
            'result_of': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'results'", 'blank': 'True', 'to': "orm['query.Query']"}),
            'source': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'source_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'subjectivity': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '2', 'decimal_places': '1'}),
            'want_rule': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'wants'", 'null': 'True', 'to': "orm['query.Rule']"})
        },
        'query.query': {
            'Meta': {'ordering': "['-created_on']", 'object_name': 'Query'},
            'count': ('django.db.models.fields.IntegerField', [], {'default': '100'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interval': ('django.db.models.fields.IntegerField', [], {'default': '1800'}),
            'last_run': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'latitude': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'num_times_run': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'query_exception': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'radius': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'throttle': ('django.db.models.fields.FloatField', [], {'default': '0.5'})
        },
        'query.rule': {
            'Meta': {'object_name': 'Rule'},
            'confidence': ('django.db.models.fields.DecimalField', [], {'default': '1.0', 'max_digits': '2', 'decimal_places': '1'}),
            'grammar': ('django.db.models.fields.IntegerField', [], {}),
            'grammar_version': ('django.db.models.fields.DecimalField', [], {'max_digits': '2', 'decimal_places': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rule': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        }
    }

    complete_apps = ['query']