# -*- coding: utf-8 -*-


from django.db import models, migrations

def default_allowed_sources_take_2(apps, schema_editor):

    Source = apps.get_model('dash', 'Source')
    all_sources = Source.objects.filter(deprecated=False)
    default_allowed_sources_list = [s.id for s in all_sources]

    Account = apps.get_model('dash', 'Account')

    accounts_count = Account.objects.all().count()

    for i, account in enumerate(Account.objects.all()):
        account.allowed_sources.add(*default_allowed_sources_list)

        print('Account settings saved - {0} of {1}'.format(i+1, accounts_count))

    print('Done.')


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0002_auto_20151215_1353'),
    ]

    operations = [
        migrations.RunPython(default_allowed_sources_take_2)
    ]
