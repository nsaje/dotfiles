# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

# looks like get_model does not return 
# the model defined in dash/models.py
# so I had to write my own
def get_current_settings(account):
    try:
        return account.settings.all().order_by('-created_dt')[0]
    except:
        return None

def default_allowed_sources(apps, schema_editor):

    Source = apps.get_model('dash', 'Source')
    all_sources = Source.objects.filter(deprecated=False)
    default_allowed_sources_list = [s.id for s in all_sources]

    Account = apps.get_model('dash', 'Account')

    accounts_count = Account.objects.all().count()

    for i, account in enumerate(Account.objects.all()):
        account_settings = get_current_settings(account)
        if account_settings is None:
            print 'No settings for account {0}'.format(account.id)
            continue

        account_settings.allowed_sources = default_allowed_sources_list
        account_settings.save()
        print 'Account settings saved - {0} of {1}'.format(i+1, accounts_count)

    print 'Done.'


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0092_merge'),
    ]

    operations = [
        migrations.RunPython(default_allowed_sources),
    ]
