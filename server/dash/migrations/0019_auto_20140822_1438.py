# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0018_auto_20140819_1250'),
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
            name='iab_category',
            field=models.SlugField(default=b'IAB24', max_length=5, choices=[(b'IAB19', b'IAB19 - Technology & Computing'), (b'IAB12', b'IAB12 - News'), (b'IAB13', b'IAB13 - Personal Finance'), (b'IAB10', b'IAB10 - Home & Garden'), (b'IAB11', b'IAB11 - Law, Government & Politics'), (b'IAB16', b'IAB16 - Pets'), (b'IAB17', b'IAB17 - Sports'), (b'IAB14', b'IAB14 - Society'), (b'IAB15', b'IAB15 - Science'), (b'IAB1', b'IAB1 - Arts & Entertainment'), (b'IAB2', b'IAB2 - Automotive'), (b'IAB3', b'IAB3 - Business'), (b'IAB4', b'IAB4 - Careers'), (b'IAB5', b'IAB5 - Education'), (b'IAB6', b'IAB6 - Family & Parenting'), (b'IAB7', b'IAB7 - Health & Fitness'), (b'IAB8', b'IAB8 - Food & Drink'), (b'IAB9', b'IAB9 - Hobbies & Interests'), (b'IAB18', b'IAB18 - Style & Fashion'), (b'IAB24', b'IAB24 - Uncategorized'), (b'IAB23', b'IAB23 - Religion & Spirituality'), (b'IAB22', b'IAB22 - Shopping'), (b'IAB21', b'IAB21 - Real Estate'), (b'IAB20', b'IAB20 - Travel')]),
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='service_fee',
            field=models.DecimalField(default=Decimal('0.2000'), max_digits=5, decimal_places=4),
        ),
    ]
