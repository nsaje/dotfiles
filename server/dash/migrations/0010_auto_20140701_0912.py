# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0009_auto_20140627_1507'),
    ]

    operations = [
        migrations.CreateModel(
            name='NetworkCredentials',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('network', models.ForeignKey(to='dash.Network', to_field=b'id')),
                ('name', models.CharField(max_length=127)),
                ('credentials', models.TextField(blank=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
            ],
            options={
                'verbose_name_plural': b'Network Credentials',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='adgroupnetwork',
            name='network_credentials',
            field=models.ForeignKey(to='dash.NetworkCredentials', to_field=b'id', null=True),
            preserve_default=True,
        ),
    ]
