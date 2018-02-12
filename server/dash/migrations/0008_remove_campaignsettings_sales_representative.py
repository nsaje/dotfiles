# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0007_auto_20151230_1007'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='campaignsettings',
            name='sales_representative',
        ),
    ]
