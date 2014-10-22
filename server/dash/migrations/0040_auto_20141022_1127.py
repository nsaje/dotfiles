# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0039_demotoreal'),
    ]

    operations = [
        migrations.CreateModel(
            name='DemoAdGroupRealAdGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('multiplication_factor', models.IntegerField(default=1)),
                ('demo_ad_group', models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroup')),
                ('real_ad_group', models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroup')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='demotoreal',
            name='demo_ad_group',
        ),
        migrations.RemoveField(
            model_name='demotoreal',
            name='real_ad_group',
        ),
        migrations.DeleteModel(
            name='DemoToReal',
        ),
    ]
