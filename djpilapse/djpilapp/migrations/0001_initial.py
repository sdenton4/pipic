# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'pilapse_project'
        db.create_table(u'djpilapp_pilapse_project', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('project_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('folder', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('Keep images', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('brightness', self.gf('django.db.models.fields.IntegerField')()),
            ('interval', self.gf('django.db.models.fields.IntegerField')()),
            ('width', self.gf('django.db.models.fields.IntegerField')()),
            ('height', self.gf('django.db.models.fields.IntegerField')()),
            ('maxtime', self.gf('django.db.models.fields.IntegerField')()),
            ('maxshots', self.gf('django.db.models.fields.IntegerField')()),
            ('delta', self.gf('django.db.models.fields.IntegerField')()),
            ('listen', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'djpilapp', ['pilapse_project'])

        # Adding model 'timelapser'
        db.create_table(u'djpilapp_timelapser', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uid', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['djpilapp.pilapse_project'])),
            ('ss', self.gf('django.db.models.fields.IntegerField')()),
            ('iso', self.gf('django.db.models.fields.IntegerField')()),
            ('lastbr', self.gf('django.db.models.fields.IntegerField')()),
            ('shots_taken', self.gf('django.db.models.fields.IntegerField')()),
            ('boot', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'djpilapp', ['timelapser'])


    def backwards(self, orm):
        # Deleting model 'pilapse_project'
        db.delete_table(u'djpilapp_pilapse_project')

        # Deleting model 'timelapser'
        db.delete_table(u'djpilapp_timelapser')


    models = {
        u'djpilapp.pilapse_project': {
            'Keep images': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Meta': {'object_name': 'pilapse_project'},
            'brightness': ('django.db.models.fields.IntegerField', [], {}),
            'delta': ('django.db.models.fields.IntegerField', [], {}),
            'folder': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'height': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interval': ('django.db.models.fields.IntegerField', [], {}),
            'listen': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'maxshots': ('django.db.models.fields.IntegerField', [], {}),
            'maxtime': ('django.db.models.fields.IntegerField', [], {}),
            'project_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'width': ('django.db.models.fields.IntegerField', [], {})
        },
        u'djpilapp.timelapser': {
            'Meta': {'object_name': 'timelapser'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'boot': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
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