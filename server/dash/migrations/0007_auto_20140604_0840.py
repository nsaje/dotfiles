# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0006_auto_20140603_2150'),
    ]

    operations = [
        migrations.CreateModel(
            name='Network',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('slug', models.SlugField(max_length=127, editable=False)),
                ('name', models.CharField(max_length=127)),
                ('created_dt', models.DateTimeField(auto_now_add=True)),
                ('modified_dt', models.DateTimeField(auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name='adgroupnetworksettings',
            name='network',
            field=models.ForeignKey(to='dash.Network', to_field=b'id'),
        ),
    ]
