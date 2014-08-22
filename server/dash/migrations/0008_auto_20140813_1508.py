# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0007_auto_20140813_1028'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='service_fee',
            field=models.DecimalField(default=0.2, max_digits=5, decimal_places=4, choices=[(b'15%', 0.15), (b'20%', 0.2), (b'20.5%', 0.205), (b'22.33%', 0.2233), (b'25%', 0.25)]),
        ),
    ]
