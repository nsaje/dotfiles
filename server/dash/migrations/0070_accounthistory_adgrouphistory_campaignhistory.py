# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-06-06 10:44


from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dash', '0069_auto_20160601_1628'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('changes_text', models.TextField()),
                ('changes', jsonfield.fields.JSONField()),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('system_user', models.PositiveSmallIntegerField(blank=True, choices=[(1, b'Campaign Stop'), (2, b'Zemanta Autopilot')], null=True)),
                ('type', models.PositiveSmallIntegerField(choices=[(2, b'Credit History'), (1, b'Account History')])),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='history', to='dash.Account')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AdGroupHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('changes_text', models.TextField()),
                ('changes', jsonfield.fields.JSONField()),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('system_user', models.PositiveSmallIntegerField(blank=True, choices=[(1, b'Campaign Stop'), (2, b'Zemanta Autopilot')], null=True)),
                ('type', models.PositiveSmallIntegerField(choices=[(2, b'Ad Group Source History'), (1, b'Ad Group History'), (3, b'Ad Group Source State History')])),
                ('ad_group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='history', to='dash.AdGroup')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CampaignHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('changes_text', models.TextField()),
                ('changes', jsonfield.fields.JSONField()),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('system_user', models.PositiveSmallIntegerField(blank=True, choices=[(1, b'Campaign Stop'), (2, b'Zemanta Autopilot')], null=True)),
                ('type', models.PositiveSmallIntegerField(choices=[(2, b'Budget History'), (1, b'Campaign History')])),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='history', to='dash.Campaign')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
