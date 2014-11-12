# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def forwards(apps, schema_editor):
    Source = apps.get_model('dash', 'Source')
    SourceType = apps.get_model('dash', 'SourceType')
    for source in Source.objects.all():
        try:
            source_type = SourceType.objects.get(type=source.type)
        except SourceType.DoesNotExist:
            source_type = SourceType.objects.create(type=source.type)

        source.source_type = source_type
        source.save()


def reverse_code(apps, schema_editor):
    Source = apps.get_model('dash', 'Source')
    for source in Source.objects.all():
        source.type = source.source_type.type
        source.save()


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0047_add_sourcetype_to_source'),
    ]

    operations = [
        migrations.RunPython(
            code=forwards,
            reverse_code=reverse_code
        )
    ]
