# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    def conversions_to_int(apps, schema_editor):
        ContentAdGoalConversionStats = apps.get_model("reports", "ContentAdGoalConversionStats")
        for stats in ContentAdGoalConversionStats.objects.all():
            stats.conversions_int = int(stats.conversions)
            stats.save()

    dependencies = [
        ('reports', '0017_auto_20150817_1343'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentadgoalconversionstats',
            name='conversions_int',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='contentadpostclickstats',
            name='bounced_visits',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='contentadpostclickstats',
            name='new_visits',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='contentadpostclickstats',
            name='pageviews',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='contentadpostclickstats',
            name='total_time_on_site',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='contentadpostclickstats',
            name='visits',
            field=models.IntegerField(null=True),
        ),
        migrations.RunPython(conversions_to_int)
    ]
