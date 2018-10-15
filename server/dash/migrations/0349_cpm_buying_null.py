# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-09-25 14:14
from __future__ import unicode_literals

from django.db import migrations
from django.db import connection


AD_GROUP_SETTINGS_BACKFILL_SQL = """
UPDATE dash_adgroupsettings ags
SET     b1_sources_group_cpm = '0.0100'
WHERE   b1_sources_group_cpm IS NULL AND ags.id BETWEEN %s AND %s;
"""

SET_AD_GROUP_NOT_NULL = """
ALTER TABLE dash_adgroupsettings
ALTER COLUMN b1_sources_group_cpm
SET NOT NULL;
"""

SOURCE_BACKFILL_SQL = """
UPDATE dash_source src
SET     default_cpm = '0.6000'
WHERE   default_cpm IS NULL AND src.id BETWEEN %s AND %s;

UPDATE  dash_source src
SET     default_mobile_cpm = '0.6000'
WHERE   default_mobile_cpm IS NULL AND src.id BETWEEN %s AND %s;
"""

SET_SOURCE_NOT_NULL = """
ALTER TABLE dash_source
ALTER COLUMN default_cpm
SET NOT NULL;

ALTER TABLE dash_source
ALTER COLUMN default_mobile_cpm
SET NOT NULL;
"""

BATCH_SIZE = 100000


def ad_group_settings_backfill(apps, schema_editor):
    with connection.cursor() as c:
        c.execute("SELECT MAX(id) FROM dash_adgroupsettings")
        count = c.fetchone()[0] or 0
        for i in range(0, count, BATCH_SIZE):
            c.execute("BEGIN")
            print("Updating ids between %s and %s" % (i, i + BATCH_SIZE))
            c.execute(AD_GROUP_SETTINGS_BACKFILL_SQL, [i, i + BATCH_SIZE])
            c.execute("COMMIT")
        c.execute("BEGIN")
        print("Altering adgroupsettings table")
        c.execute(SET_AD_GROUP_NOT_NULL)
        c.execute("COMMIT")


def source_backfill(apps, schema_editor):
    with connection.cursor() as c:
        c.execute("SELECT MAX(id) FROM dash_source")
        count = c.fetchone()[0] or 0
        for i in range(0, count, BATCH_SIZE):
            c.execute("BEGIN")
            print("Updating ids between %s and %s" % (i, i + BATCH_SIZE))
            c.execute(SOURCE_BACKFILL_SQL, [i, i + BATCH_SIZE, i, i + BATCH_SIZE])
            c.execute("COMMIT")
        c.execute("BEGIN")
        print("Altering source table")
        c.execute(SET_SOURCE_NOT_NULL)
        c.execute("COMMIT")


class Migration(migrations.Migration):

    dependencies = [("dash", "0348_publisherclassification")]

    operations = [
        migrations.RunPython(ad_group_settings_backfill),
        migrations.RunPython(source_backfill),
    ]