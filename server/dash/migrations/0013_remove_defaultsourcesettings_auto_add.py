# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0012_auto_20160115_0927'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='defaultsourcesettings',
            name='auto_add',
        ),
    ]
