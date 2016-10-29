# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-10-27 13:14
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import jsonfield.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportJob',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('status', models.IntegerField(choices=[(2, b'Failed'), (1, b'Done'), (4, b'Cancelled'), (3, b'In progress')], default=3)),
                ('query', jsonfield.fields.JSONField()),
                ('result', jsonfield.fields.JSONField(blank=True, null=True)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
