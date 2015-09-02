# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0066_add_batch_fields_to_contentad'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='conversion_pixels',
            field=models.ManyToManyField(to='dash.ConversionPixel'),
        ),
    ]
