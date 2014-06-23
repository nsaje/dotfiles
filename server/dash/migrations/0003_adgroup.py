# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dash', '0002_campaign'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdGroup',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=127)),
                ('campaign', models.ForeignKey(to='dash.Campaign', to_field=b'id')),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('modified_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field='id')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
