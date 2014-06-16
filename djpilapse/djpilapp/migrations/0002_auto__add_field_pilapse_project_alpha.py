# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'pilapse_project.alpha'
        db.add_column(u'djpilapp_pilapse_project', 'alpha',
                      self.gf('django.db.models.fields.FloatField')(default=0.01),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'pilapse_project.alpha'
        db.delete_column(u'djpilapp_pilapse_project', 'alpha')


    models = {
        u'djpilapp.pilapse_project': {
            'Keep images': ('django.db.models.fields.BooleanField', [], {}),
            'Meta': {'object_name': 'pilapse_project'},
            'alpha': ('django.db.models.fields.FloatField', [], {}),
            'brightness': ('django.db.models.fields.IntegerField', [], {}),
            'delta': ('django.db.models.fields.IntegerField', [], {}),
            'folder': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'height': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interval': ('django.db.models.fields.IntegerField', [], {}),
            'listen': ('django.db.models.fields.BooleanField', [], {}),
            'maxshots': ('django.db.models.fields.IntegerField', [], {}),
            'maxtime': ('django.db.models.fields.IntegerField', [], {}),
            'project_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'width': ('django.db.models.fields.IntegerField', [], {})
        },
        u'djpilapp.timelapser': {
            'Meta': {'object_name': 'timelapser'},
            'active': ('django.db.models.fields.BooleanField', [], {}),
            'boot': ('django.db.models.fields.BooleanField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'iso': ('django.db.models.fields.IntegerField', [], {}),
            'lastbr': ('django.db.models.fields.IntegerField', [], {}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['djpilapp.pilapse_project']"}),
            'shots_taken': ('django.db.models.fields.IntegerField', [], {}),
            'ss': ('django.db.models.fields.IntegerField', [], {}),
            'uid': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['djpilapp']