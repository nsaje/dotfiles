# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0010_sourcetype_cpc_decimal_places'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContentAd',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image_id', models.CharField(max_length=256, null=True, editable=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UploadBatch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=1024)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
            ],
            options={
                'get_latest_by': 'created_dt',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='contentad',
            name='batch',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dash.UploadBatch', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='article',
            name='batch',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dash.UploadBatch', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='article',
            name='content_ad',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT, to='dash.ContentAd'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='article',
            name='image_id',
            field=models.CharField(max_length=256, null=True, editable=False),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='article',
            unique_together=None,
        ),
        migrations.RunSQL('CREATE UNIQUE INDEX dash_article_url_title_ad_group_id_content_ad_id_uniq ON dash_article (url, title, ad_group_id, content_ad_id) WHERE content_ad_id IS NOT NULL'),
        migrations.RunSQL('CREATE UNIQUE INDEX dash_article_url_title_ad_group_id_uniq ON dash_article (url, title, ad_group_id) WHERE content_ad_id IS NULL'),
    ]
