# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-08 10:22
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0238_remove_scheduledreport_last_sent_dt'),
    ]

    operations = [
        migrations.CreateModel(
            name='PublisherBidModifier',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('publisher', models.CharField(max_length=127, verbose_name=b'Publisher name or domain')),
                ('modifier', models.FloatField(verbose_name=b'Publisher bid modifier')),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('ad_group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroup')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dash.Source')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='publisherbidmodifier',
            unique_together=set([('ad_group', 'source', 'publisher')]),
        ),
    ]
