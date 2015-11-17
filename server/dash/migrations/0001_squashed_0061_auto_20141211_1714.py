# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
from decimal import Decimal
import django.db.models.deletion
from django.conf import settings
import dash.models


# Functions from the following migrations need manual copying.
# Move them and any dependencies into this file, then update the
# RunPython operations to refer to the local versions:

# dash.migrations.0054_ad_group_state_initial_data
def ad_group_state_initial_data_forwards_copy_settings(apps, schema_editor):
    AdGroupSourceSettings = apps.get_model('dash', 'AdGroupSourceSettings')
    AdGroupSourceState = apps.get_model('dash', 'AdGroupSourceState')

    if len(AdGroupSourceState.objects.all()) > 0:
        return

    latest_settings = AdGroupSourceSettings.objects.\
        distinct('ad_group_source_id').\
        order_by('ad_group_source_id', '-created_dt')

    for settings in latest_settings:
        AdGroupSourceState.objects.create(
            ad_group_source=settings.ad_group_source,
            created_dt=settings.created_dt,
            state=settings.state,
            cpc_cc=settings.cpc_cc,
            daily_budget_cc=settings.daily_budget_cc
        )


def ad_group_state_initial_data_reverse_copy_settings(apps, schema_editor):
    pass


# dash.migrations.0051_source_action_initial_data
def source_action_initial_data_forwards_code(apps, schema_editor):
    SourceAction = apps.get_model('dash', 'SourceAction')
    for source_action in dash.constants.SourceAction.get_all():
        try:
            SourceAction.objects.get(action=source_action)
        except SourceAction.DoesNotExist:
            SourceAction.objects.create(action=source_action)


def source_action_initial_data_reverse_code(apps, schema_editor):
    pass


# dash.migrations.0048_move_type_data_to_source_type
def move_type_data_to_source_type_forwards(apps, schema_editor):
    Source = apps.get_model('dash', 'Source')
    SourceType = apps.get_model('dash', 'SourceType')
    for source in Source.objects.all():
        try:
            source_type = SourceType.objects.get(type=source.type)
        except SourceType.DoesNotExist:
            source_type = SourceType.objects.create(type=source.type)

        source.source_type = source_type
        source.save()


def move_type_data_to_source_type_reverse_code(apps, schema_editor):
    Source = apps.get_model('dash', 'Source')
    for source in Source.objects.all():
        source.type = source.source_type.type
        source.save()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=127)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('modified_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT)),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AdGroup',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=127)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('modified_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AdGroupSettings',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('state', models.IntegerField(default=2, choices=[(1, b'Enabled'), (2, b'Paused')])),
                ('start_date', models.DateField(null=True, blank=True)),
                ('end_date', models.DateField(null=True, blank=True)),
                ('cpc_cc', models.DecimalField(null=True, verbose_name=b'CPC', max_digits=10, decimal_places=4, blank=True)),
                ('daily_budget_cc', models.DecimalField(null=True, verbose_name=b'Daily budget', max_digits=10, decimal_places=4, blank=True)),
                ('target_devices', jsonfield.fields.JSONField(default=[], blank=True)),
                ('target_regions', jsonfield.fields.JSONField(default=[], blank=True)),
                ('tracking_code', models.TextField(blank=True)),
                ('ad_group', models.ForeignKey(to='dash.AdGroup', on_delete=django.db.models.deletion.PROTECT)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'ordering': (b'-created_dt',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AdGroupSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('source_campaign_key', jsonfield.fields.JSONField(default={}, blank=True)),
                ('ad_group', models.ForeignKey(to='dash.AdGroup', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AdGroupSourceSettings',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('state', models.IntegerField(default=2, choices=[(1, b'Enabled'), (2, b'Paused')])),
                ('cpc_cc', models.DecimalField(null=True, verbose_name=b'CPC', max_digits=10, decimal_places=4, blank=True)),
                ('daily_budget_cc', models.DecimalField(null=True, verbose_name=b'Daily budget', max_digits=10, decimal_places=4, blank=True)),
                ('ad_group_source', models.ForeignKey(related_name=b'settings', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroupSource', null=True)),
                ('created_by', models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': (b'-created_dt',),
                'get_latest_by': b'created_dt',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.CharField(max_length=2048, editable=False)),
                ('title', models.CharField(max_length=256, editable=False)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('ad_group', models.ForeignKey(to='dash.AdGroup', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'get_latest_by': b'created_dt',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='article',
            unique_together=set([(b'ad_group', b'url', b'title')]),
        ),
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=127)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('account', models.ForeignKey(to='dash.Account', on_delete=django.db.models.deletion.PROTECT)),
                ('modified_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT)),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model, dash.models.PermissionMixin),
        ),
        migrations.AddField(
            model_name='adgroup',
            name='campaign',
            field=models.ForeignKey(to='dash.Campaign', on_delete=django.db.models.deletion.PROTECT),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('type', models.CharField(max_length=127, null=True, blank=True)),
                ('name', models.CharField(max_length=127)),
                ('maintenance', models.BooleanField(default=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='adgroupsource',
            name='source',
            field=models.ForeignKey(to='dash.Source', on_delete=django.db.models.deletion.PROTECT),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='adgroup',
            name='sources',
            field=models.ManyToManyField(to=b'dash.Source', through='dash.AdGroupSource'),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='SourceCredentials',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=127)),
                ('credentials', models.TextField(blank=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('source', models.ForeignKey(to='dash.Source', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'verbose_name_plural': b'Source Credentials',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='adgroupsource',
            name='source_credentials',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dash.SourceCredentials', null=True),
            preserve_default=True,
        ),
        migrations.AlterModelOptions(
            name='adgroupsettings',
            options={'ordering': (b'-created_dt',), 'permissions': ((b'settings_view', b'Can view settings in dashboard.'),)},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={'permissions': ((b'chart_legend_view', b'Can view chart legend in Media Sources tab.'),)},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.CreateModel(
            name='CampaignSettings',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('service_fee', models.DecimalField(default=0.2, max_digits=5, decimal_places=4, choices=[(b'15%', 0.15), (b'20%', 0.2), (b'20.5%', 0.205), (b'22.33%', 0.2233), (b'25%', 0.25)])),
                ('iab_category', models.IntegerField(default=24, choices=[(4, b'Careers'), (5, b'Education'), (7, b'Health & Fitness'), (1, b'Arts & Entertainment'), (2, b'Automotive'), (3, b'Business'), (8, b'Food & Drink'), (6, b'Family & Parenting'), (9, b'Hobbies & Interests'), (10, b'Home & Garden'), (19, b'Technology & Computing'), (18, b'Style & Fashion'), (16, b'Pets'), (17, b'Sports'), (14, b'Society'), (15, b'Science'), (12, b'News'), (13, b'Personal Finance'), (11, b'Law, Government & Politics'), (24, b'Uncategorized'), (23, b'Religion & Spirituality'), (22, b'Shopping'), (21, b'Real Estate'), (20, b'Travel')])),
                ('promotion_goal', models.IntegerField(default=1, choices=[(3, b'Conversions'), (1, b'Brand Building'), (2, b'Traffic Acquisition')])),
                ('account_manager', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True)),
                ('campaign', models.ForeignKey(to='dash.Campaign', on_delete=django.db.models.deletion.PROTECT)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT)),
                ('sales_representative', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True)),
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
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='service_fee',
            field=models.DecimalField(default=0.2, max_digits=5, decimal_places=4, choices=[(0.15, b'15%'), (0.2, b'20%'), (0.205, b'20.5%'), (0.2233, b'22.33%'), (0.25, b'25%')]),
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterModelOptions(
            name='account',
            options={'permissions': ((b'account_automatically_assigned', b'All new accounts are automatically added to user.'),)},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={'permissions': ((b'campaign_automatically_assigned', b'All new campaigns are automatically added to user.'),)},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='account',
            options={},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AddField(
            model_name='account',
            name='groups',
            field=models.ManyToManyField(to=b'auth.Group'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='campaign',
            name='groups',
            field=models.ManyToManyField(to=b'auth.Group'),
            preserve_default=True,
        ),
        migrations.AlterModelOptions(
            name='account',
            options={'ordering': (b'-created_dt',), 'permissions': ((b'group_account_automatically_add', b'All new accounts are automatically added to group.'),)},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='service_fee',
            field=models.DecimalField(default=0.2, max_digits=5, decimal_places=4, choices=[(Decimal('0.15'), b'15%'), (Decimal('0.2'), b'20%'), (Decimal('0.205'), b'20.5%'), (Decimal('0.2233'), b'22.33%'), (Decimal('0.25'), b'25%')]),
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='account_manager',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='sales_representative',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='account_manager',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='sales_representative',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AddField(
            model_name='campaignsettings',
            name='name',
            field=models.CharField(default=None, max_length=127),
            preserve_default=False,
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='iab_category',
            field=models.SlugField(default=b'IAB24', max_length=5, choices=[(b'IAB19', b'IAB19 - Technology & Computing'), (b'IAB12', b'IAB12 - News'), (b'IAB13', b'IAB13 - Personal Finance'), (b'IAB10', b'IAB10 - Home & Garden'), (b'IAB11', b'IAB11 - Law, Government & Politics'), (b'IAB16', b'IAB16 - Pets'), (b'IAB17', b'IAB17 - Sports'), (b'IAB14', b'IAB14 - Society'), (b'IAB15', b'IAB15 - Science'), (b'IAB1', b'IAB1 - Arts & Entertainment'), (b'IAB2', b'IAB2 - Automotive'), (b'IAB3', b'IAB3 - Business'), (b'IAB4', b'IAB4 - Careers'), (b'IAB5', b'IAB5 - Education'), (b'IAB6', b'IAB6 - Family & Parenting'), (b'IAB7', b'IAB7 - Health & Fitness'), (b'IAB8', b'IAB8 - Food & Drink'), (b'IAB9', b'IAB9 - Hobbies & Interests'), (b'IAB18', b'IAB18 - Style & Fashion'), (b'IAB24', b'IAB24 - Uncategorized'), (b'IAB23', b'IAB23 - Religion & Spirituality'), (b'IAB22', b'IAB22 - Shopping'), (b'IAB21', b'IAB21 - Real Estate'), (b'IAB20', b'IAB20 - Travel')]),
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='service_fee',
            field=models.DecimalField(default=Decimal('0.2000'), max_digits=5, decimal_places=4),
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.CreateModel(
            name='DefaultSourceSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('credentials', models.ForeignKey(to='dash.SourceCredentials', on_delete=django.db.models.deletion.PROTECT)),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dash.Source', unique=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AddField(
            model_name='adgroupsource',
            name='last_successful_sync_dt',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterModelOptions(
            name='defaultsourcesettings',
            options={'verbose_name_plural': b'Default Source Credentials'},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterModelOptions(
            name='defaultsourcesettings',
            options={'verbose_name_plural': b'Default Source Settings'},
        ),
        migrations.AddField(
            model_name='defaultsourcesettings',
            name='params',
            field=jsonfield.fields.JSONField(default={}, help_text=b'Information about format can be found here: <a href="https://sites.google.com/a/zemanta.com/root/content-ads-dsp/additional-source-parameters-format" target="_blank">Zemanta Pages</a>', verbose_name=b'Additional action parameters', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='defaultsourcesettings',
            name='credentials',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.SourceCredentials', null=True),
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterField(
            model_name='defaultsourcesettings',
            name='source',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='dash.Source'),
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterField(
            model_name='account',
            name='modified_by',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='adgroup',
            name='modified_by',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='adgroupsettings',
            name='ad_group',
            field=models.ForeignKey(related_name=b'settings', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroup'),
        ),
        migrations.AlterField(
            model_name='adgroupsettings',
            name='created_by',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='modified_by',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='account_manager',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='campaign',
            field=models.ForeignKey(related_name=b'settings', on_delete=django.db.models.deletion.PROTECT, to='dash.Campaign'),
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='created_by',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='sales_representative',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='account',
            name='modified_by',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='adgroup',
            name='modified_by',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='adgroupsettings',
            name='ad_group',
            field=models.ForeignKey(related_name=b'settings', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroup'),
        ),
        migrations.AlterField(
            model_name='adgroupsettings',
            name='created_by',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='modified_by',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='account_manager',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='campaign',
            field=models.ForeignKey(related_name=b'settings', on_delete=django.db.models.deletion.PROTECT, to='dash.Campaign'),
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='created_by',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='sales_representative',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.CreateModel(
            name='CampaignBudgetSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('allocate', models.DecimalField(default=0, verbose_name=b'Allocate amount', max_digits=20, decimal_places=4)),
                ('revoke', models.DecimalField(default=0, verbose_name=b'Revoke amount', max_digits=20, decimal_places=4)),
                ('total', models.DecimalField(default=0, verbose_name=b'Total budget', max_digits=20, decimal_places=4)),
                ('comment', models.CharField(max_length=256)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('campaign', models.ForeignKey(to='dash.Campaign', on_delete=django.db.models.deletion.PROTECT)),
                ('created_by', models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'get_latest_by': 'created_dt',
            },
            bases=(models.Model,),
        ),
        migrations.AlterModelOptions(
            name='campaignbudgetsettings',
            options={'ordering': ('-created_dt',), 'get_latest_by': 'created_dt'},
        ),
        migrations.CreateModel(
            name='AccountSettings',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=127)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('archived', models.BooleanField(default=False)),
                ('account', models.ForeignKey(related_name=b'settings', on_delete=django.db.models.deletion.PROTECT, to='dash.Account')),
                ('created_by', models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_dt',),
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='adgroupsettings',
            name='archived',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='campaignsettings',
            name='archived',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='DemoAdGroupRealAdGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('multiplication_factor', models.IntegerField(default=1)),
                ('demo_ad_group', models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroup', unique=True)),
                ('real_ad_group', models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroup', unique=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='adgroup',
            name='is_demo',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={'ordering': ('name',)},
        ),
        migrations.CreateModel(
            name='AdGroupSourceState',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('state', models.IntegerField(default=2, choices=[(1, b'Enabled'), (2, b'Paused')])),
                ('cpc_cc', models.DecimalField(null=True, verbose_name=b'CPC', max_digits=10, decimal_places=4, blank=True)),
                ('daily_budget_cc', models.DecimalField(null=True, verbose_name=b'Daily budget', max_digits=10, decimal_places=4, blank=True)),
                ('ad_group_source', models.ForeignKey(related_name=b'states', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroupSource', null=True)),
            ],
            options={
                'ordering': ('-created_dt',),
                'get_latest_by': 'created_dt',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SourceType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(unique=True, max_length=127)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='source',
            name='source_type',
            field=models.ForeignKey(to='dash.SourceType', null=True),
            preserve_default=True,
        ),
        migrations.RunPython(
            code=move_type_data_to_source_type_forwards,
            reverse_code=move_type_data_to_source_type_reverse_code,
            atomic=True,
        ),
        migrations.RemoveField(
            model_name='source',
            name='type',
        ),
        migrations.CreateModel(
            name='SourceAction',
            fields=[
                ('action', models.IntegerField(serialize=False, primary_key=True, choices=[(3, b'Can update daily budget'), (1, b'Can update state'), (2, b'Can update CPC')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RunPython(
            code=source_action_initial_data_forwards_code,
            reverse_code=source_action_initial_data_reverse_code,
            atomic=True,
        ),
        migrations.AddField(
            model_name='sourcetype',
            name='available_actions',
            field=models.ManyToManyField(to=b'dash.SourceAction', blank=True),
            preserve_default=True,
        ),
        migrations.AlterModelOptions(
            name='sourcetype',
            options={'verbose_name': 'Source Type', 'verbose_name_plural': 'Source Types'},
        ),
        migrations.AddField(
            model_name='accountsettings',
            name='changes_text',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='adgroupsettings',
            name='changes_text',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.RunPython(
            code=ad_group_state_initial_data_forwards_copy_settings,
            reverse_code=ad_group_state_initial_data_reverse_copy_settings,
            atomic=True,
        ),
        migrations.AlterField(
            model_name='adgroupsourcesettings',
            name='state',
            field=models.IntegerField(null=True, choices=[(1, b'Enabled'), (2, b'Paused')]),
        ),
        migrations.AlterField(
            model_name='adgroupsourcesettings',
            name='state',
            field=models.IntegerField(null=True, choices=[(1, b'Enabled'), (2, b'Paused')]),
        ),
        migrations.AddField(
            model_name='sourcetype',
            name='min_cpc',
            field=models.DecimalField(null=True, verbose_name=b'Minimum CPC', max_digits=10, decimal_places=4, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='sourcetype',
            name='min_daily_budget',
            field=models.DecimalField(null=True, verbose_name=b'Minimum Daily Budget', max_digits=10, decimal_places=4, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='sourcetype',
            name='max_cpc',
            field=models.DecimalField(null=True, verbose_name=b'Maximum CPC', max_digits=10, decimal_places=4, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='sourcetype',
            name='max_daily_budget',
            field=models.DecimalField(null=True, verbose_name=b'Maximum Daily Budget', max_digits=10, decimal_places=4, blank=True),
            preserve_default=True,
        ),
    ]
