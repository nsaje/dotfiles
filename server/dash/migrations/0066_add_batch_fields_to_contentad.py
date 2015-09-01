# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations




def forward_copy_from_batch_to_content_ad(apps, schema_editor):
    # we will copy the fields display_url, brand_name, description and call_to_action from UploadBatch to ContentAd
    ContentAd = apps.get_model("dash", "ContentAd")
    for contentad in ContentAd.objects.all():
        contentad.display_url = contentad.batch.display_url
        contentad.brand_name = contentad.batch.brand_name
        contentad.description = contentad.batch.description
        contentad.call_to_action = contentad.batch.call_to_action
        contentad.save()
        
def backward_copy_from_batch_to_content_ad(apps, schema_editor):
    # data can simply get discarded
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0065_auto_20150828_1151'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentad',
            name='brand_name',
            field=models.CharField(default=b'', max_length=25, blank=True),
        ),
        migrations.AddField(
            model_name='contentad',
            name='call_to_action',
            field=models.CharField(default=b'', max_length=25, blank=True),
        ),
        migrations.AddField(
            model_name='contentad',
            name='description',
            field=models.CharField(default=b'', max_length=140, blank=True),
        ),
        migrations.AddField(
            model_name='contentad',
            name='display_url',
            field=models.CharField(default=b'', max_length=25, blank=True),
        ),
        migrations.RunPython(forward_copy_from_batch_to_content_ad, backward_copy_from_batch_to_content_ad),
         
    ]
