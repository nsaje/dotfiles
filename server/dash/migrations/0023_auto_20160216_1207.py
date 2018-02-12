# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0022_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='uses_credits',
            field=models.BooleanField(default=True, verbose_name=b'Uses credits and budgets accounting'),
        ),
    ]
