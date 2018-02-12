# -*- coding: utf-8 -*-


from django.db import migrations
from dash.constants import EmailTemplateType


def load_data(apps, schema_editor):
    EmailTemplate = apps.get_model('dash', 'EmailTemplate')

    try:
        template = EmailTemplate.objects.get(template_type=EmailTemplateType.DEMO_RUNNING)
    except EmailTemplate.DoesNotExist:
        template = EmailTemplate(subject='Demo is running', template_type=EmailTemplateType.DEMO_RUNNING)

    template.body = '''Hi,

Demo is running.
Log in to {url}
u/p: regular.user+demo@zemanta.com / {password}

Note: This instance will selfdestroy in 7 days

Yours truly,
Zemanta
    '''
    template.save()


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0143_auto_20161110_1523'),
    ]

    operations = [
        migrations.RunPython(load_data)
    ]
