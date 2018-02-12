# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-08-05 09:30


from django.db import migrations, models

from dash.constants import EmailTemplateType

def load_data(apps, schema_editor):
    EmailTemplate = apps.get_model('dash', 'EmailTemplate')

    livestream = EmailTemplate.objects.get(template_type=EmailTemplateType.LIVESTREAM_SESSION)
    livestream.recipients = 'operations@zemanta.com, ziga.stopinsek@zemanta.com'
    livestream.save()

    EmailTemplate(
        template_type=EmailTemplateType.DAILY_MANAGEMENT_REPORT,
        subject='Daily management report',
        body='Please use an email client with HTML support.',
        recipients='ziga.stopinsek@zemanta.com, bostjan@zemanta.com, urska.kosec@zemanta.com',
    ).save()

class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0105_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailtemplate',
            name='recipients',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='emailtemplate',
            name='template_type',
            field=models.PositiveSmallIntegerField(blank=True, choices=[(2, b'Campaign settings change'), (3, b'Budget change'), (12, b'Autopilot initialisation notification'), (5, b'User password reset'), (6, b'New user introduction email'), (4, b'New conversion pixel'), (8, b'Scheduled report'), (7, b'Supply report'), (16, b'Livestream sesion id'), (17, b'Daily management report'), (1, b'Ad group settings change'), (14, b'Campaign is running out of budget notification'), (9, b'Depleting budget notification'), (15, b'Demo is running'), (10, b'Campaign stopped notification'), (13, b'Campaign switched to landing mode notification'), (11, b'Autopilot changes notification')], null=True),
        ),
        migrations.RunPython(load_data),
    ]
