# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Pin'
        db.create_table('pins_pin', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.TextField')()),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('pins', ['Pin'])

    def backwards(self, orm):
        # Deleting model 'Pin'
        db.delete_table('pins_pin')

    models = {
        'pins.pin': {
            'Meta': {'ordering': "['-id']", 'object_name': 'Pin'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'url': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['pins']