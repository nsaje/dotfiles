# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0008_auto_20140604_0847'),
    ]

    operations = [
        migrations.AlterField(
            model_name='network',
            name='slug',
            field=models.SlugField(max_length=127, editable=False),
        ),
    ]
