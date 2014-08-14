# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0011_merge'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='service_fee',
            field=models.DecimalField(default=0.2, max_digits=5, decimal_places=4, choices=[(Decimal('0.15'), b'15%'), (Decimal('0.2'), b'20%'), (Decimal('0.205'), b'20.5%'), (Decimal('0.2233'), b'22.33%'), (Decimal('0.25'), b'25%')]),
        ),
    ]
