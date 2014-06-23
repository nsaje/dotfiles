# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import dash.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dash', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=127)),
                ('account', models.ForeignKey(to='dash.Account', to_field=b'id')),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('modified_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field='id')),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model, dash.models.PermissionMixin),
        ),
    ]
