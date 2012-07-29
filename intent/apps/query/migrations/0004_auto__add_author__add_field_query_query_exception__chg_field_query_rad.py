# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Author'
        db.create_table('query_author', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('twitter_handle', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=40)),
        ))
        db.send_create_signal('query', ['Author'])

        # Adding field 'Query.query_exception'
        db.add_column('query_query', 'query_exception',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True),
                      keep_default=False)


        # Changing field 'Query.radius'
        db.alter_column('query_query', 'radius', self.gf('django.db.models.fields.CharField')(default='', max_length=40))

        # Changing field 'Query.longitude'
        db.alter_column('query_query', 'longitude', self.gf('django.db.models.fields.CharField')(default='', max_length=40))

        # Changing field 'Query.latitude'
        db.alter_column('query_query', 'latitude', self.gf('django.db.models.fields.CharField')(default='', max_length=40))
        # Deleting field 'Document.profile'
        db.delete_column('query_document', 'profile')

        # Deleting field 'Document.description'
        db.delete_column('query_document', 'description')

        # Deleting field 'Document.language'
        db.delete_column('query_document', 'language')

        # Deleting field 'Document.author'
        db.delete_column('query_document', 'author')

        # Deleting field 'Document.url'
        db.delete_column('query_document', 'url')

        # Adding M2M table for field author on 'Document'
        db.create_table('query_document_author', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('document', models.ForeignKey(orm['query.document'], null=False)),
            ('author', models.ForeignKey(orm['query.author'], null=False))
        ))
        db.create_unique('query_document_author', ['document_id', 'author_id'])

        # Adding unique constraint on 'Document', fields ['source_id']
        db.create_unique('query_document', ['source_id'])

    def backwards(self, orm):
        # Removing unique constraint on 'Document', fields ['source_id']
        db.delete_unique('query_document', ['source_id'])

        # Deleting model 'Author'
        db.delete_table('query_author')

        # Deleting field 'Query.query_exception'
        db.delete_column('query_query', 'query_exception')


        # Changing field 'Query.radius'
        db.alter_column('query_query', 'radius', self.gf('django.db.models.fields.CharField')(max_length=40, null=True))

        # Changing field 'Query.longitude'
        db.alter_column('query_query', 'longitude', self.gf('django.db.models.fields.CharField')(max_length=40, null=True))

        # Changing field 'Query.latitude'
        db.alter_column('query_query', 'latitude', self.gf('django.db.models.fields.CharField')(max_length=40, null=True))

        # User chose to not deal with backwards NULL issues for 'Document.profile'
        raise RuntimeError("Cannot reverse this migration. 'Document.profile' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'Document.description'
        raise RuntimeError("Cannot reverse this migration. 'Document.description' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'Document.language'
        raise RuntimeError("Cannot reverse this migration. 'Document.language' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'Document.author'
        raise RuntimeError("Cannot reverse this migration. 'Document.author' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'Document.url'
        raise RuntimeError("Cannot reverse this migration. 'Document.url' and its values cannot be restored.")
        # Removing M2M table for field author on 'Document'
        db.delete_table('query_document_author')

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
            'author': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['query.Author']", 'symmetrical': 'False'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dislike_rule': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'dislikes'", 'blank': 'True', 'to': "orm['query.Rule']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'intent': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'modality': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '2', 'decimal_places': '1'}),
            'polarity': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '2', 'decimal_places': '1'}),
            'promise_rule': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'promises'", 'blank': 'True', 'to': "orm['query.Rule']"}),
            'question_rule': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'questions'", 'blank': 'True', 'to': "orm['query.Rule']"}),
            'result_of': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'results'", 'blank': 'True', 'to': "orm['query.Query']"}),
            'source': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'source_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'subjectivity': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '2', 'decimal_places': '1'}),
            'want_rule': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'wants'", 'blank': 'True', 'to': "orm['query.Rule']"})
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