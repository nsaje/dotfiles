# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-09 11:21
from __future__ import unicode_literals

from django.db import migrations

from dash import constants


DEFAULT_ADVERTISER_ID = '953699'


def create_default_yahoo_account(apps, schema_editor):

    Account = apps.get_model('dash', 'Account')
    YahooAccount = apps.get_model('dash', 'YahooAccount')

    default_yahoo_account = YahooAccount.objects.create(
        advertiser_id=DEFAULT_ADVERTISER_ID,
        budgets_tz='America/Los_Angeles',
        currency=constants.Currency.USD
    )
    Account.objects.filter(yahoo_account__isnull=True).update(
        yahoo_account=default_yahoo_account)


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0303_merge_20180509_0811'),
    ]

    operations = [
        migrations.RunPython(create_default_yahoo_account)
    ]
