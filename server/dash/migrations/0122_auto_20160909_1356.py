# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-09-09 13:56


from django.db import migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0121_auto_20160907_1422'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroupsettings',
            name='audience_targeting',
            field=jsonfield.fields.JSONField(blank=True, default=[]),
        ),
        migrations.AddField(
            model_name='adgroupsettings',
            name='exclusion_audience_targeting',
            field=jsonfield.fields.JSONField(blank=True, default=[]),
        ),
    ]
