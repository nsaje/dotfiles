# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('actionlog', '0007_actionlog_message'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActionLogOrder',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('state', models.IntegerField(default=1, choices=[(2, b'Success'), (-1, b'Failed'), (1, b'Waiting')])),
                ('order_type', models.IntegerField(choices=[(1, b'Fetch all')])),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at', null=True)),
                ('modified_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Modified at', null=True)),
                ('created_by', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('modified_by', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='actionlog',
            name='order',
            field=models.ForeignKey(to='actionlog.ActionLogOrder', null=True),
            preserve_default=True,
        ),
    ]
