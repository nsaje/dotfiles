# Generated by Django 2.1.11 on 2021-01-11 08:54

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("dash", "0510_merge_20210107_0843")]

    operations = [
        migrations.RemoveField(model_name="creativetag", name="count"),
        migrations.RemoveField(model_name="creativetag", name="label"),
        migrations.RemoveField(model_name="creativetag", name="level"),
        migrations.RemoveField(model_name="creativetag", name="parent"),
        migrations.RemoveField(model_name="creativetag", name="path"),
        migrations.RemoveField(model_name="creativetag", name="protected"),
        migrations.RemoveField(model_name="creativetag", name="slug"),
        migrations.AlterField(model_name="creative", name="tags", field=models.ManyToManyField(to="dash.CreativeTag")),
        migrations.AlterField(
            model_name="creativebatch", name="default_tags", field=models.ManyToManyField(to="dash.CreativeTag")
        ),
        migrations.AlterField(
            model_name="creativebatch",
            name="original_filename",
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
        migrations.AlterField(
            model_name="creativecandidate", name="tags", field=models.ManyToManyField(to="dash.CreativeTag")
        ),
    ]
