# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-02-01 10:10


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0273_auto_20180130_1538'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campaignsettings',
            name='language',
            field=models.SlugField(choices=[(b'sv', b'Swedish'), (b'pt', b'Portuguese'), (b'tr', b'Turkish'), (b'de', b'German'), (b'en', b'English'), (b'id', b'Indonesian'), (b'fr', b'French'), (b'ja', b'Japanese'), (b'el', b'Greek'), (b'any', b'Other'), (b'nl', b'Dutch'), (b'ar', b'Arabic'), (b'zh_TW', b'Traditional Chinese'), (b'it', b'Italian'), (b'vi', b'Vietnamese'), (b'ro', b'Romanian'), (b'zh_CN', b'Simplified Chinese'), (b'ms', b'Malay'), (b'es', b'Spanish'), (b'ru', b'Russian')], default=b'en'),
        ),
    ]
