# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0003_auto_20140626_1540'),
        ('dash', '0008_article')
    ]

    operations = [
        migrations.AlterField(
            model_name='articlestats',
            name='article',
            field=models.ForeignKey(to='dash.Article', to_field='id'),
        ),
        migrations.DeleteModel(
            name='Article',
        ),
    ]
