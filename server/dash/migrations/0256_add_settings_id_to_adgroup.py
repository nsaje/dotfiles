# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-11-23 15:27


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0255_add_settings_id_to_campaign'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroup',
            name='new_settings',
            field=models.ForeignKey(blank=True, db_column='settings_id', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='latest_for_ad_group', to='dash.AdGroupSettings'),
        ),
    ]
