# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
import django.db.models.deletion
from django.conf import settings
import dash.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dash', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=127)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('modified_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT)),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AdGroup',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=127)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('modified_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AdGroupSettings',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('state', models.IntegerField(default=2, choices=[(1, b'Enabled'), (2, b'Paused')])),
                ('start_date', models.DateField(null=True, blank=True)),
                ('end_date', models.DateField(null=True, blank=True)),
                ('cpc_cc', models.DecimalField(null=True, verbose_name=b'CPC', max_digits=10, decimal_places=4, blank=True)),
                ('daily_budget_cc', models.DecimalField(null=True, verbose_name=b'Daily budget', max_digits=10, decimal_places=4, blank=True)),
                ('target_devices', jsonfield.fields.JSONField(default=[], blank=True)),
                ('target_regions', jsonfield.fields.JSONField(default=[], blank=True)),
                ('tracking_code', models.TextField(blank=True)),
                ('ad_group', models.ForeignKey(to='dash.AdGroup', on_delete=django.db.models.deletion.PROTECT)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'ordering': (b'-created_dt',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AdGroupSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('source_campaign_key', jsonfield.fields.JSONField(default={}, blank=True)),
                ('ad_group', models.ForeignKey(to='dash.AdGroup', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AdGroupSourceSettings',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('state', models.IntegerField(default=2, choices=[(1, b'Enabled'), (2, b'Paused')])),
                ('cpc_cc', models.DecimalField(null=True, verbose_name=b'CPC', max_digits=10, decimal_places=4, blank=True)),
                ('daily_budget_cc', models.DecimalField(null=True, verbose_name=b'Daily budget', max_digits=10, decimal_places=4, blank=True)),
                ('ad_group_source', models.ForeignKey(to='dash.AdGroupSource', on_delete=django.db.models.deletion.PROTECT, null=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': (b'-created_dt',),
                'get_latest_by': b'created_dt',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.CharField(max_length=2048, editable=False)),
                ('title', models.CharField(max_length=256, editable=False)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('ad_group', models.ForeignKey(to='dash.AdGroup', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'get_latest_by': b'created_dt',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='article',
            unique_together=set([(b'ad_group', b'url', b'title')]),
        ),
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=127)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('account', models.ForeignKey(to='dash.Account', on_delete=django.db.models.deletion.PROTECT)),
                ('modified_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT)),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model, dash.models.PermissionMixin),
        ),
        migrations.AddField(
            model_name='adgroup',
            name='campaign',
            field=models.ForeignKey(to='dash.Campaign', on_delete=django.db.models.deletion.PROTECT),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('type', models.CharField(max_length=127, null=True, blank=True)),
                ('name', models.CharField(max_length=127)),
                ('maintenance', models.BooleanField(default=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='adgroupsource',
            name='source',
            field=models.ForeignKey(to='dash.Source', on_delete=django.db.models.deletion.PROTECT),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='adgroup',
            name='sources',
            field=models.ManyToManyField(to='dash.Source', through='dash.AdGroupSource'),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='SourceCredentials',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=127)),
                ('credentials', models.TextField(blank=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('source', models.ForeignKey(to='dash.Source', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'verbose_name_plural': b'Source Credentials',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='adgroupsource',
            name='source_credentials',
            field=models.ForeignKey(to='dash.SourceCredentials', on_delete=django.db.models.deletion.PROTECT, null=True),
            preserve_default=True,
        ),
    ]
