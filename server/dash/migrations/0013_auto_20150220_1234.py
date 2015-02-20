# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0012_auto_20150217_1342'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContentAdSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('submission_status', models.IntegerField(default=1, choices=[(3, b'Rejected'), (2, b'Approved'), (1, b'Pending')])),
                ('state', models.IntegerField(default=2, choices=[(1, b'Enabled'), (2, b'Paused')])),
                ('source_state', models.IntegerField(default=2, choices=[(1, b'Enabled'), (2, b'Paused')])),
                ('source_content_ad_id', models.CharField(max_length=50, null=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('content_ad', models.ForeignKey(to='dash.ContentAd', on_delete=django.db.models.deletion.PROTECT)),
                ('source', models.ForeignKey(to='dash.Source', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='contentad',
            name='bidder_id',
            field=models.IntegerField(null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='contentad',
            name='sources',
            field=models.ManyToManyField(to='dash.Source', through='dash.ContentAdSource'),
            preserve_default=True,
        ),
    ]
