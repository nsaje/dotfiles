# Generated by Django 2.1.11 on 2020-09-02 13:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("dash", "0476_merge_20200826_1110")]

    operations = [
        migrations.RemoveField(model_name="yahoomigrationadgrouphistory", name="ad_group"),
        migrations.RemoveField(model_name="yahoomigrationcontentadhistory", name="content_ad"),
        migrations.RemoveField(model_name="account", name="yahoo_account"),
        migrations.RemoveField(model_name="agency", name="yahoo_account"),
        migrations.DeleteModel(name="YahooAccount"),
        migrations.DeleteModel(name="YahooMigrationAdGroupHistory"),
        migrations.DeleteModel(name="YahooMigrationContentAdHistory"),
    ]