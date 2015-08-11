# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def copy_source_actions(apps, schema_editor):
    SourceType = apps.get_model('dash', 'SourceType')
    for st in SourceType.objects.all():
        st.available_actions = st.available_actions_new
        st.save()


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0062_sourcetype_available_actions'),
    ]

    operations = [
        migrations.RunPython(copy_source_actions)
    ]
