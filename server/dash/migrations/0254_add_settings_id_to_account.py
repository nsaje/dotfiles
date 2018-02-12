# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-11-23 15:27


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0253_campaign_real_time_campaign_stop'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='new_settings',
            field=models.ForeignKey(blank=True, db_column='settings_id', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='latest_for_account', to='dash.AccountSettings'),
        ),
    ]
