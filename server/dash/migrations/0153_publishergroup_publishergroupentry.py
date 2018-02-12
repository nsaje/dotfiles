# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2017-01-11 10:18


from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dash', '0152_auto_20170106_1015'),
    ]

    operations = [
        migrations.CreateModel(
            name='PublisherGroup',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=127)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='dash.Account')),
                ('agency', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='dash.Agency')),
                ('modified_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PublisherGroupEntry',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('publisher', models.CharField(max_length=127, verbose_name=b'Publisher name or domain')),
                ('outbrain_publisher_id', models.CharField(blank=True, max_length=127, verbose_name=b'Special Outbrain publisher ID')),
                ('publisher_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entries', to='dash.PublisherGroup')),
                ('source', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='dash.Source')),
            ],
        ),
    ]
