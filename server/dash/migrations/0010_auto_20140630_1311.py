# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0009_auto_20140627_1507'),
    ]

    operations = [
        migrations.CreateModel(
            name='NetworkCredentials',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=127)),
                ('credentials', jsonfield.fields.JSONField(default={})),
                ('network', models.ForeignKey(to='dash.Network', to_field=b'id')),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='adgroupnetwork',
            name='credentials',
            field=models.ForeignKey(to='dash.NetworkCredentials', to_field=b'id', null=True),
            preserve_default=True,
        ),
    ]
