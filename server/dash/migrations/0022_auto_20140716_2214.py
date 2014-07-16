# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0011_auto_20140716_2214'),
        ('actionlog', '0018_auto_20140716_2214'),
        ('dash', '0021_auto_20140716_1508'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='adgroup',
            name='networks',
        ),
        migrations.DeleteModel(
            name='AdGroupNetworkSettings',
        ),
        migrations.DeleteModel(
            name='AdGroupNetwork',
        ),
        migrations.DeleteModel(
            name='NetworkCredentials',
        ),
        migrations.DeleteModel(
            name='Network',
        ),
        migrations.AlterField(
            model_name='adgroup',
            name='created_dt',
            field=models.DateTimeField(auto_now_add=True, verbose_name=b'Created at'),
        ),
        migrations.AlterField(
            model_name='adgroup',
            name='modified_dt',
            field=models.DateTimeField(auto_now=True, verbose_name=b'Modified at'),
        ),
        migrations.AlterField(
            model_name='adgroupsourcesettings',
            name='created_dt',
            field=models.DateTimeField(auto_now_add=True, verbose_name=b'Created at'),
        ),
        migrations.AlterField(
            model_name='source',
            name='created_dt',
            field=models.DateTimeField(auto_now_add=True, verbose_name=b'Created at'),
        ),
        migrations.AlterField(
            model_name='source',
            name='modified_dt',
            field=models.DateTimeField(auto_now=True, verbose_name=b'Modified at'),
        ),
        migrations.AlterField(
            model_name='sourcecredentials',
            name='created_dt',
            field=models.DateTimeField(auto_now_add=True, verbose_name=b'Created at'),
        ),
        migrations.AlterField(
            model_name='sourcecredentials',
            name='modified_dt',
            field=models.DateTimeField(auto_now=True, verbose_name=b'Modified at'),
        ),
    ]
