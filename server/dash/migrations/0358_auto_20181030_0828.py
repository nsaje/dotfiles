# Generated by Django 2.1.2 on 2018-10-30 08:28

from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [("dash", "0357_cachedonetoonefield")]

    operations = [
        migrations.RunSQL(
            "create index concurrently dash_contentadsource_cadid_sid ON dash_contentadsource (content_ad_id, source_id)"
        )
    ]
