# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dash', '0005_auto_20140724_1638'),
    ]

    operations = [
        migrations.CreateModel(
            name='CampaignSettings',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('service_fee', models.DecimalField(verbose_name=b'Service Fee', max_digits=4, decimal_places=2)),
                ('iab_category', models.IntegerField(default=24, choices=[(4, b'Careers'), (5, b'Education'), (7, b'Health & Fitness'), (1, b'Arts & Entertainment'), (2, b'Automotive'), (3, b'Business'), (8, b'Food & Drink'), (6, b'Family & Parenting'), (9, b'Hobbies & Interests'), (10, b'Home & Garden'), (19, b'Technology & Computing'), (18, b'Style & Fashion'), (16, b'Pets'), (17, b'Sports'), (14, b'Society'), (15, b'Science'), (12, b'News'), (13, b'Personal Finance'), (11, b'Law, Government & Politics'), (24, b'Uncategorized'), (23, b'Religion & Spirituality'), (22, b'Shopping'), (21, b'Real Estate'), (20, b'Travel')])),
                ('promotion_goal', models.IntegerField(default=1, choices=[(3, b'Conversions'), (1, b'Brand Building'), (2, b'Traffic Acquisition')])),
                ('account_manager', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT)),
                ('campaign', models.ForeignKey(to='dash.Campaign', on_delete=django.db.models.deletion.PROTECT)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT)),
                ('sales_representative', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'ordering': (b'-created_dt',),
                'permissions': ((b'campaign_settings_view', b'Can view campaign settings in dashboard.'),),
            },
            bases=(models.Model,),
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
    ]
