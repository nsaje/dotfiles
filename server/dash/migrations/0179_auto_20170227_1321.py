# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-27 13:21


from django.db import migrations


def set_implicit_flag(apps, schema_editor):
    PublisherGroup = apps.get_model("dash", "PublisherGroup")

    for pg in PublisherGroup.objects.all():
        implicit = pg.name.startswith('Default whitelist for') or \
            pg.name.startswith('Default blacklist for')

        pg.implicit = implicit
        pg.save(None)


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0178_publishergroup_implicit'),
    ]

    operations = [
        migrations.RunPython(set_implicit_flag)
    ]
