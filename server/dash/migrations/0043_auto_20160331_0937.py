# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0042_auto_20160325_1007'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='adgroupsourcesettings',
            name='system_user',
        ),
        migrations.AddField(
            model_name='adgroupsourcesettings',
            name='landing_mode',
            field=models.BooleanField(default=False),
        ),
    ]
