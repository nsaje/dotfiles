# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0001_initial'),
        ('dash', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArticleStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField()),
                ('ad_group', models.ForeignKey(to='dash.AdGroup', to_field=b'id')),
                ('article', models.ForeignKey(to='reports.Article', to_field='id')),
                ('network', models.ForeignKey(to='dash.Network', to_field=b'id')),
                ('impressions', models.IntegerField(default=0)),
                ('clicks', models.IntegerField(default=0)),
                ('cpc_cc', models.IntegerField(default=0)),
                ('cost_cc', models.IntegerField(default=0)),
            ],
            options={
                'unique_together': set([(b'date', b'ad_group', b'article', b'network')]),
            },
            bases=(models.Model,),
        ),
    ]
