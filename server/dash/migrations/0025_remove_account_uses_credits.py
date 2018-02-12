# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0024_merge'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='account',
            name='uses_credits',
        ),
    ]
