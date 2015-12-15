# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(unique=True, max_length=255, verbose_name='email address')),
                ('username', models.CharField(blank=True, help_text='30 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=30, verbose_name='username', validators=[django.core.validators.RegexValidator(b'^[\\w.@+-]+$', 'Enter a valid username.', b'invalid')])),
                ('first_name', models.CharField(max_length=30, verbose_name='first name', blank=True)),
                ('last_name', models.CharField(max_length=30, verbose_name='last name', blank=True)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('show_onboarding_guidance', models.BooleanField(default=False, help_text=b'Designates whether user has self-manage access and needs onboarding guidance.')),
                ('groups', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'permissions': (('campaign_settings_view', "Can view campaign's settings tab."), ('campaign_agency_view', "Can view campaign's agency tab."), ('campaign_ad_groups_view', "Can view campaign's ad groups tab in dashboard."), ('campaign_budget_view', "Can view campaign's budget tab."), ('campaign_settings_account_manager', 'Can be chosen as account manager.'), ('campaign_settings_sales_rep', 'Can be chosen as sales representative.'), ('supply_dash_link_view', 'Can view supply dash link.'), ('ad_group_agency_tab_view', "Can view ad group's agency tab."), ('all_accounts_accounts_view', "Can view all accounts's accounts tab."), ('account_campaigns_view', "Can view accounts's campaigns tab."), ('account_agency_view', "Can view accounts's agency tab."), ('account_credit_view', "Can view accounts's credit tab."), ('ad_group_sources_add_source', 'Can add media sources.'), ('campaign_sources_view', 'Can view campaign sources view.'), ('account_sources_view', 'Can view account sources view.'), ('all_accounts_sources_view', 'Can view all accounts sources view.'), ('campaign_ad_groups_add_ad_group', 'Can add ad groups.'), ('account_campaigns_add_campaign', 'Can add campaigns.'), ('all_accounts_accounts_add_account', 'Can add accounts.'), ('all_new_sidebar', 'Can see new sidebar.'), ('campaign_budget_management_view', 'Can do campaign budget management.'), ('account_budget_view', 'Can view account budget.'), ('all_accounts_budget_view', 'Can view all accounts budget.'), ('archive_restore_entity', 'Can archive or restore an entity.'), ('view_archived_entities', 'Can view archived entities.'), ('unspent_budget_view', 'Can view unspent budget.'), ('switch_to_demo_mode', 'Can switch to demo mode.'), ('account_agency_access_permissions', 'Can view and set account access permissions.'), ('group_new_user_add', 'New users are added to this group.'), ('set_ad_group_source_settings', 'Can set per-source settings.'), ('see_current_ad_group_source_state', 'Can see current per-source state.'), ('campaign_ad_groups_detailed_report', 'Can download detailed report on campaign level.'), ('content_ads_postclick_acquisition', 'Can view content ads postclick acq. metrics.'), ('content_ads_postclick_engagement', 'Can view content ads postclick eng. metrics.'), ('aggregate_postclick_acquisition', 'Can view aggregate postclick acq. metrics.'), ('aggregate_postclick_engagement', 'Can view aggregate postclick eng. metrics.'), ('data_status_column', 'Can see data status column in table.'), ('new_content_ads_tab', 'Can view new content ads tab.'), ('filter_sources', 'Can filter sources'), ('upload_content_ads', 'Can upload new content ads.'), ('set_content_ad_status', 'Can set status of content ads.'), ('get_content_ad_csv', 'Can download bulk content ad csv.'), ('content_ads_bulk_actions', 'Can view and use bulk content ads actions.'), ('can_toggle_ga_performance_tracking', 'Can toggle Google Analytics performance tracking.'), ('can_toggle_adobe_performance_tracking', 'Can toggle Adobe Analytics performance tracking.'), ('can_see_media_source_status_on_submission_popover', 'Can see media source status on submission status popover'), ('can_set_subdivision_targeting', 'Can set subdivision targeting'), ('can_set_media_source_to_auto_pilot', 'Can set media source to auto-pilot'), ('manage_conversion_pixels', 'Can manage conversion pixels'), ('add_media_sources_automatically', 'Automatically add media sources on ad group creation'), ('has_intercom', 'Can see intercom widget'), ('can_see_publishers', 'Can see publishers'), ('manage_conversion_goals', 'Can manage conversion goals on campaign level'), ('can_see_redshift_postclick_statistics', 'Can see Redshift postclick statistics'), ('group_campaign_stop_on_budget_depleted', 'Automatic campaign stop on depleted budget applies to campaigns in this group'), ('can_see_publisher_blacklist_status', 'Can see publishers blacklist status'), ('can_modify_publisher_blacklist_status', 'Can modify publishers blacklist status'), ('conversion_reports', 'Can see conversions and goals in reports'), ('exports_plus', 'Can download reports using new export facilities'), ('can_modify_allowed_sources', 'Can modify allowed sources on account level'), ('settings_defaults_on_campaign_level', 'Can view ad group settings defaults on campaign level'), ('can_access_global_publisher_blacklist_status', 'Can view or modify global publishers blacklist status'), ('can_access_campaign_account_publisher_blacklist_status', 'Can view or modify account and campaign publishers blacklist status'), ('can_view_data_cost', 'Can view or export data cost'), ('can_see_all_available_sources', 'Can see all available media sources in account settings'), ('can_see_infobox', 'Can see info box'), ('account_account_view', "Can view account's Account tab.")),
            },
        ),
        migrations.CreateModel(
            name='InternalGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='auth.Group')),
            ],
        ),
        migrations.RunSQL(
            sql='CREATE UNIQUE INDEX zemauth_user_email_idx ON zemauth_user (lower(email));',
            reverse_sql=None,
            state_operations=None,
        ),
    ]
