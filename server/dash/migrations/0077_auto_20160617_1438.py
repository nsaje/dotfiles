# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-06-17 14:38


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0076_auto_20160617_1146'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='history',
            options={'verbose_name': 'History', 'verbose_name_plural': 'History'},
        ),
        migrations.AddField(
            model_name='adgroupsourcesettings',
            name='system_user',
            field=models.PositiveSmallIntegerField(blank=True, choices=[(1, b'Campaign Stop'), (2, b'Zemanta Autopilot')], null=True),
        ),
    ]
