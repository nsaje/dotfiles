# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Network',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('slug', models.SlugField(max_length=127, editable=False)),
                ('name', models.CharField(max_length=127)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=127)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('modified_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field='id')),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
