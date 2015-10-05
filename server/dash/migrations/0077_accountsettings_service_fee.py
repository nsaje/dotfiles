# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0076_auto_20150925_0813'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountsettings',
            name='service_fee',
            field=models.DecimalField(default=Decimal('0.2000'), max_digits=5, decimal_places=4),
        ),
    ]
