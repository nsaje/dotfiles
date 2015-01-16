# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    replaces = [(b'zemauth', '0001_initial'), (b'zemauth', '0002_auto_20140717_1425'), (b'zemauth', '0003_auto_20140811_1139'), (b'zemauth', '0004_internalgroup'), (b'zemauth', '0005_auto_20140819_1508'), (b'zemauth', '0006_auto_20140820_0825'), (b'zemauth', '0007_auto_20140820_1322'), (b'zemauth', '0008_auto_20140820_1337'), (b'zemauth', '0003_auto_20140813_1623'), (b'zemauth', '0004_auto_20140813_1625'), (b'zemauth', '0005_merge'), (b'zemauth', '0006_auto_20140814_1330'), (b'zemauth', '0009_merge'), (b'zemauth', '0007_merge'), (b'zemauth', '0010_merge'), (b'zemauth', '0008_auto_20140822_1438'), (b'zemauth', '0012_merge'), (b'zemauth', '0011_auto_20140822_1117'), (b'zemauth', '0013_merge'), (b'zemauth', '0014_auto_20140825_1212'), (b'zemauth', '0013_auto_20140825_1306'), (b'zemauth', '0015_merge'), (b'zemauth', '0016_auto_20140828_0921'), (b'zemauth', '0017_auto_20140828_1048'), (b'zemauth', '0018_auto_20140828_1253'), (b'zemauth', '0019_auto_20140828_1629'), (b'zemauth', '0020_auto_20140916_0832'), (b'zemauth', '0021_auto_20140922_1619'), (b'zemauth', '0021_auto_20140919_1012'), (b'zemauth', '0022_merge'), (b'zemauth', '0022_auto_20140924_1411'), (b'zemauth', '0023_merge'), (b'zemauth', '0024_auto_20140930_0959'), (b'zemauth', '0025_auto_20140930_1312'), (b'zemauth', '0026_auto_20141014_1213'), (b'zemauth', '0027_auto_20141016_1535'), (b'zemauth', '0028_auto_20141027_1111'), (b'zemauth', '0029_auto_20141027_1337'), (b'zemauth', '0030_auto_20141112_1044'), (b'zemauth', '0030_auto_20141110_1510'), (b'zemauth', '0031_merge'), (b'zemauth', '0032_auto_20141113_0927'), (b'zemauth', '0031_auto_20141112_1647'), (b'zemauth', '0033_merge'), (b'zemauth', '0034_auto_20141117_1236'), (b'zemauth', '0035_auto_20141203_1519'), (b'zemauth', '0036_auto_20141209_1103'), (b'zemauth', '0037_auto_20141217_1407'), (b'zemauth', '0038_auto_20150108_1153')]

    dependencies = [
        ('auth', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(default=django.utils.timezone.now, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(unique=True, max_length=255, verbose_name='email address')),
                ('username', models.CharField(blank=True, help_text='30 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=30, verbose_name='username', validators=[django.core.validators.RegexValidator(b'^[\\w.@+-]+$', 'Enter a valid username.', b'invalid')])),
                ('first_name', models.CharField(max_length=30, verbose_name='first name', blank=True)),
                ('last_name', models.CharField(max_length=30, verbose_name='last name', blank=True)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('groups', models.ManyToManyField(to=b'auth.Group', verbose_name='groups', blank=True)),
                ('user_permissions', models.ManyToManyField(to=b'auth.Permission', verbose_name='user permissions', blank=True)),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
            bases=(models.Model,),
        ),
        migrations.RunSQL(
            sql='ALTER TABLE zemauth_user DROP CONSTRAINT zemauth_user_email_key;',
            reverse_sql=None,
            state_operations=None,
        ),
        migrations.RunSQL(
            sql='CREATE UNIQUE INDEX zemauth_user_email_idx ON zemauth_user (lower(email));',
            reverse_sql=None,
            state_operations=None,
        ),
        migrations.AlterModelOptions(
            name='user',
            options={'verbose_name': 'user', 'verbose_name_plural': 'users', 'permissions': ((b'help_view', b'Can view help popovers.'),)},
        ),
        migrations.CreateModel(
            name='InternalGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='auth.Group', unique=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterModelOptions(
            name='user',
            options={'verbose_name': 'user', 'verbose_name_plural': 'users', 'permissions': ((b'help_view', b'Can view help popovers.'), (b'supply_dash_link_view', b'Can view supply dash link.'))},
        ),
        migrations.AlterField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(related_query_name='user', related_name='user_set', to=b'auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of his/her group.', verbose_name='groups'),
        ),
        migrations.AlterField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(related_query_name='user', related_name='user_set', to=b'auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions'),
        ),
        migrations.AlterModelOptions(
            name='user',
            options={'verbose_name': 'user', 'verbose_name_plural': 'users', 'permissions': (('campaign_settings_view', 'Can view campaign settings in dashboard.'), ('campaign_ad_groups_view', "Can view campaign's ad groups tab in dashboard."), ('campaign_settings_account_manager', 'Can be chosen as account manager.'), ('campaign_settings_sales_rep', 'Can be chosen as sales representative.'), ('help_view', 'Can view help popovers.'), ('supply_dash_link_view', 'Can view supply dash link.'), ('ad_group_agency_tab_view', "Can view ad group's agency tab."), ('all_accounts_accounts_view', "Can view all accounts's accounts tab."), ('account_campaigns_view', "Can view accounts's campaigns tab."), ('account_agency_view', "Can view accounts's agency tab."), ('ad_group_sources_add_source', 'Can add media sources.'), ('campaign_sources_view', 'Can view campaign sources view.'), ('account_sources_view', 'Can view account sources view.'), ('all_accounts_sources_view', 'Can view all accounts sources view.'), ('campaign_ad_groups_add_ad_group', 'Can add ad groups.'), ('account_campaigns_add_campaign', 'Can add campaigns.'), ('all_accounts_accounts_add_account', 'Can add accounts.'), ('all_new_sidebar', 'Can see new sidebar.'), ('campaign_budget_management_view', 'Can do campaign budget management.'), ('account_budget_view', 'Can view account budget.'), ('all_accounts_budget_view', 'Can view all accounts budget.'), ('archive_restore_entity', 'Can archive or restore an entity.'), ('view_archived_entities', 'Can view archived entities.'), ('unspent_budget_view', 'Can view unspent budget.'), ('switch_to_demo_mode', 'Can switch to demo mode.'), ('account_agency_access_permissions', 'Can view and set account access permissions.'), ('group_new_user_add', 'New users are added to this group.'), ('set_ad_group_source_settings', 'Can set per-source settings.'), ('see_current_ad_group_source_state', 'Can see current per-source state.'), ('has_intercom', 'Can see intercom.io widget'), ('campaign_ad_groups_detailed_report', 'Can download detailed report on campaign level.'), ('content_ads_postclick_acquisition', 'Can view content ads postclick acq. metrics.'), ('content_ads_postclick_engagement', 'Can view content ads postclick eng. metrics.'), ('aggregate_postclick_acquisition', 'Can view aggregate postclick acq. metrics.'), ('aggregate_postclick_engagement', 'Can view aggregate postclick eng. metrics.'), ('data_status_column', 'Can see data status column in table.'))},
        ),
    ]
