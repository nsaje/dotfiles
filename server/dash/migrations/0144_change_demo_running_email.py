# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from dash.constants import EmailTemplateType


def load_data(apps, schema_editor):
    EmailTemplate = apps.get_model('dash', 'EmailTemplate')

    template = EmailTemplate.objects.get(template_type=EmailTemplateType.DEMO_RUNNING)
    template.body = u'''Hi,

Demo is running.
Log in to {url}
u/p: regular.user+demo@zemanta.com / {password}

Note: This instance will selfdestroy in 7 days

Yours truly,
Zemanta
    '''
    )
    template.save()


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0143_auto_20161110_1523'),
    ]

    operations = [
        migrations.RunPython(load_data)
    ]
