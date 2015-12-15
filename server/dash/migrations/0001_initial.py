# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
import jsonfield.fields
import dash.models
import django.contrib.postgres.fields
from decimal import Decimal
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=127)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('uses_credits', models.BooleanField(default=False, verbose_name=b'Uses credits and budgets accounting')),
                ('outbrain_marketer_id', models.CharField(max_length=255, null=True, blank=True)),
                ('groups', models.ManyToManyField(to='auth.Group')),
                ('modified_by', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_dt',),
                'permissions': (('group_account_automatically_add', 'All new accounts are automatically added to group.'),),
            },
        ),
        migrations.CreateModel(
            name='AccountSettings',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=127)),
                ('service_fee', models.DecimalField(default=Decimal('0.2000'), max_digits=5, decimal_places=4)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('archived', models.BooleanField(default=False)),
                ('changes_text', models.TextField(null=True, blank=True)),
                ('allowed_sources', django.contrib.postgres.fields.ArrayField(default=[], base_field=models.IntegerField(), size=None)),
                ('account', models.ForeignKey(related_name='settings', on_delete=django.db.models.deletion.PROTECT, to='dash.Account')),
                ('created_by', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('default_account_manager', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True)),
                ('default_sales_representative', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-created_dt',),
            },
        ),
        migrations.CreateModel(
            name='AdGroup',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=127)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('is_demo', models.BooleanField(default=False)),
                ('content_ads_tab_with_cms', models.BooleanField(default=True, verbose_name=b'Content ads tab with CMS')),
            ],
            options={
                'ordering': ('name',),
            },
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
                ('enable_ga_tracking', models.BooleanField(default=True)),
                ('enable_adobe_tracking', models.BooleanField(default=False)),
                ('adobe_tracking_param', models.CharField(default=b'', max_length=10, blank=True)),
                ('archived', models.BooleanField(default=False)),
                ('display_url', models.CharField(default=b'', max_length=25, blank=True)),
                ('brand_name', models.CharField(default=b'', max_length=25, blank=True)),
                ('description', models.CharField(default=b'', max_length=140, blank=True)),
                ('call_to_action', models.CharField(default=b'', max_length=25, blank=True)),
                ('ad_group_name', models.CharField(default=b'', max_length=127, blank=True)),
                ('changes_text', models.TextField(null=True, blank=True)),
                ('ad_group', models.ForeignKey(related_name='settings', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroup')),
                ('created_by', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-created_dt',),
                'permissions': (('settings_view', 'Can view settings in dashboard.'),),
            },
        ),
        migrations.CreateModel(
            name='AdGroupSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('source_campaign_key', jsonfield.fields.JSONField(default={}, blank=True)),
                ('last_successful_sync_dt', models.DateTimeField(null=True, blank=True)),
                ('last_successful_reports_sync_dt', models.DateTimeField(null=True, blank=True)),
                ('last_successful_status_sync_dt', models.DateTimeField(null=True, blank=True)),
                ('can_manage_content_ads', models.BooleanField(default=False)),
                ('source_content_ad_id', models.CharField(max_length=100, null=True, blank=True)),
                ('submission_status', models.IntegerField(default=-1, choices=[(1, b'Pending'), (4, b'Limit reached'), (-1, b'Not submitted'), (2, b'Approved'), (3, b'Rejected')])),
                ('submission_errors', models.TextField(null=True, blank=True)),
                ('ad_group', models.ForeignKey(to='dash.AdGroup', on_delete=django.db.models.deletion.PROTECT)),
            ],
        ),
        migrations.CreateModel(
            name='AdGroupSourceSettings',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('state', models.IntegerField(default=2, choices=[(1, b'Enabled'), (2, b'Paused')])),
                ('cpc_cc', models.DecimalField(null=True, verbose_name=b'CPC', max_digits=10, decimal_places=4, blank=True)),
                ('daily_budget_cc', models.DecimalField(null=True, verbose_name=b'Daily budget', max_digits=10, decimal_places=4, blank=True)),
                ('autopilot_state', models.IntegerField(default=2, choices=[(1, b'Enabled'), (2, b'Paused')])),
                ('ad_group_source', models.ForeignKey(related_name='settings', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroupSource', null=True)),
                ('created_by', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-created_dt',),
                'get_latest_by': 'created_dt',
            },
        ),
        migrations.CreateModel(
            name='AdGroupSourceState',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('state', models.IntegerField(default=2, choices=[(1, b'Enabled'), (2, b'Paused')])),
                ('cpc_cc', models.DecimalField(null=True, verbose_name=b'CPC', max_digits=10, decimal_places=4, blank=True)),
                ('daily_budget_cc', models.DecimalField(null=True, verbose_name=b'Daily budget', max_digits=10, decimal_places=4, blank=True)),
                ('ad_group_source', models.ForeignKey(related_name='states', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroupSource', null=True)),
            ],
            options={
                'ordering': ('-created_dt',),
                'get_latest_by': 'created_dt',
            },
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
                'get_latest_by': 'created_dt',
            },
        ),
        migrations.CreateModel(
            name='BudgetHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('snapshot', jsonfield.fields.JSONField()),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BudgetLineItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('amount', models.IntegerField()),
                ('comment', models.CharField(max_length=256, null=True, blank=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=127)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('account', models.ForeignKey(to='dash.Account', on_delete=django.db.models.deletion.PROTECT)),
                ('groups', models.ManyToManyField(to='auth.Group')),
                ('modified_by', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
            bases=(models.Model, dash.models.PermissionMixin),
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
                ('created_by', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_dt',),
                'get_latest_by': 'created_dt',
            },
        ),
        migrations.CreateModel(
            name='CampaignSettings',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=127)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('service_fee', models.DecimalField(default=Decimal('0.2000'), max_digits=5, decimal_places=4)),
                ('iab_category', models.SlugField(default=b'IAB24', max_length=10, choices=[(b'IAB19-34', b'Web Design/HTML'), (b'IAB19-35', b'Web Search'), (b'IAB19-36', b'Windows'), (b'IAB19-30', b'Shareware/Freeware'), (b'IAB14-8', b'Ethnic Specific'), (b'IAB19-32', b'Visual Basic'), (b'IAB19-33', b'Web Clip Art'), (b'IAB14-5', b'Senior Living'), (b'IAB14-4', b'Marriage'), (b'IAB14-7', b'Weddings'), (b'IAB14-6', b'Teens'), (b'IAB14-1', b'Dating'), (b'IAB14-3', b'Gay Life'), (b'IAB14-2', b'Divorce Support'), (b'IAB25-1', b'Unmoderated UGC'), (b'IAB25-3', b'Pornography'), (b'IAB25-2', b'Extreme Graphic/Explicit Violence'), (b'IAB12-3', b'Local News'), (b'IAB12-2', b'National News'), (b'IAB12-1', b'International News'), (b'IAB19-31', b'Unix'), (b'IAB10-1', b'Appliances'), (b'IAB10-3', b'Environmental Safety'), (b'IAB10-2', b'Entertaining'), (b'IAB10-5', b'Home Repair'), (b'IAB10-4', b'Gardening'), (b'IAB10-7', b'Interior Decorating'), (b'IAB10-6', b'Home Theater'), (b'IAB10-9', b'Remodeling & Construction'), (b'IAB10-8', b'Landscaping'), (b'IAB15-10', b'Weather'), (b'IAB17-14', b'Game & Fish'), (b'IAB17-15', b'Golf'), (b'IAB17-16', b'Horse Racing'), (b'IAB17-17', b'Horses'), (b'IAB17-10', b'Figure Skating'), (b'IAB17-11', b'Fly Fishing'), (b'IAB17-12', b'Football'), (b'IAB17-13', b'Freshwater Fishing'), (b'IAB17-18', b'Hunting/Shooting'), (b'IAB17-19', b'Inline Skating'), (b'IAB7-18', b'Depression'), (b'IAB7-19', b'Dermatology'), (b'IAB7-16', b'Deafness'), (b'IAB7-17', b'Dental Care'), (b'IAB7-14', b'Chronic Pain'), (b'IAB7-15', b'Cold & Flu'), (b'IAB7-12', b'Cholesterol'), (b'IAB7-13', b'Chronic Fatigue Syndrome'), (b'IAB7-10', b'Brain Tumor'), (b'IAB7-11', b'Cancer'), (b'IAB7-4', b'Allergies'), (b'IAB7-5', b'Alternative Medicine'), (b'IAB7-6', b'Arthritis'), (b'IAB7-7', b'Asthma'), (b'IAB7-1', b'Exercise'), (b'IAB7-2', b'A.D.D.'), (b'IAB7-3', b'AIDS/HIV'), (b'IAB7-8', b'Autism/PDD'), (b'IAB7-9', b'Bipolar Disorder'), (b'IAB1-6', b'Music'), (b'IAB1-7', b'Television'), (b'IAB1-4', b'Humor'), (b'IAB1-5', b'Movies'), (b'IAB1-2', b'Celebrity Fan/Gossip'), (b'IAB1-3', b'Fine Art'), (b'IAB1-1', b'Books & Literature'), (b'IAB25-5', b'Hate Content'), (b'IAB7-35', b'Pediatrics'), (b'IAB25-4', b'Profane Content'), (b'IAB25-7', b'Incentivized'), (b'IAB13-10', b'Retirement Planning'), (b'IAB13-11', b'Stocks'), (b'IAB13-12', b'Tax Planning'), (b'IAB25-6', b'Under Construction'), (b'IAB5-1', b'7-12 Education'), (b'IAB17-38', b'Swimming'), (b'IAB17-39', b'Table Tennis/Ping-Pong'), (b'IAB17-32', b'Saltwater Fishing'), (b'IAB17-33', b'Scuba Diving'), (b'IAB17-30', b'Running/Jogging'), (b'IAB17-31', b'Sailing'), (b'IAB17-36', b'Snowboarding'), (b'IAB17-37', b'Surfing/Bodyboarding'), (b'IAB17-34', b'Skateboarding'), (b'IAB17-35', b'Skiing'), (b'IAB5-2', b'Adult Education'), (b'IAB5-3', b'Art History'), (b'IAB19-18', b'Internet Technology'), (b'IAB19-19', b'Java'), (b'IAB5-6', b'Distance Learning'), (b'IAB5-7', b'English as a 2nd Language'), (b'IAB5-4', b'Colledge Administration'), (b'IAB5-5', b'College Life'), (b'IAB19-12', b'Databases'), (b'IAB19-13', b'Desktop Publishing'), (b'IAB5-8', b'Language Learning'), (b'IAB5-9', b'Graduate School'), (b'IAB19-16', b'Graphics Software'), (b'IAB19-17', b'Home Video/DVD'), (b'IAB19-14', b'Desktop Video'), (b'IAB19-15', b'Email'), (b'IAB2-15', b'Mororcycles'), (b'IAB2-14', b'MiniVan'), (b'IAB2-17', b'Performance Vehicles'), (b'IAB8-7', b'Cuisine-Specific'), (b'IAB19-1', b'3-D Graphics'), (b'IAB19-2', b'Animation'), (b'IAB19-3', b'Antivirus Software'), (b'IAB19-4', b'C/C++'), (b'IAB19-5', b'Cameras & Camcorders'), (b'IAB19-6', b'Cell Phones'), (b'IAB19-7', b'Computer Certification'), (b'IAB19-8', b'Computer Networking'), (b'IAB19-9', b'Computer Peripherals'), (b'IAB22-1', b'Contests & Freebies'), (b'IAB22-4', b'Engines'), (b'IAB8-8', b'Desserts & Baking'), (b'IAB17-2', b'Baseball'), (b'IAB17-3', b'Bicycling'), (b'IAB17-1', b'Auto Racing'), (b'IAB20-8', b'By US Locale'), (b'IAB20-9', b'Camping'), (b'IAB17-4', b'Bodybuilding'), (b'IAB17-5', b'Boxing'), (b'IAB20-4', b'Australia & New Zealand'), (b'IAB20-5', b'Bed & Breakfasts'), (b'IAB20-6', b'Budget Travel'), (b'IAB20-7', b'Business Travel'), (b'IAB20-1', b'Adventure Travel'), (b'IAB20-2', b'Africa'), (b'IAB20-3', b'Air Travel'), (b'IAB15-4', b'Geology'), (b'IAB15-5', b'Paranormal Phenomena'), (b'IAB15-6', b'Physics'), (b'IAB15-7', b'Space/Astronomy'), (b'IAB23', b'Religion & Spirituality'), (b'IAB15-1', b'Astrology'), (b'IAB15-2', b'Biology'), (b'IAB20', b'Travel'), (b'IAB26-4', b'CopyrightInfringement'), (b'IAB15-8', b'Geography'), (b'IAB15-9', b'Botany'), (b'IAB26-1', b'Illegal Content'), (b'IAB9-29', b'Stamps & Coins'), (b'IAB9-28', b'Screenwriting'), (b'IAB4-11', b'Career Advice'), (b'IAB4-10', b'U.S. Military'), (b'IAB9-21', b'Needlework'), (b'IAB9-20', b'Magic & Illusion'), (b'IAB9-23', b'Photography'), (b'IAB9-22', b'Painting'), (b'IAB9-25', b'Roleplaying Games'), (b'IAB9-24', b'Radio'), (b'IAB9-27', b'Scrapbooking'), (b'IAB9-26', b'Sci-Fi & Fantasy'), (b'IAB26', b'Illegal Content'), (b'IAB2-1', b'Auto Parts'), (b'IAB2-3', b'Buying/Selling Cars'), (b'IAB2-2', b'Auto Repair'), (b'IAB2-5', b'Certified Pre-Owned'), (b'IAB2-4', b'Car Culture'), (b'IAB2-7', b'Coupe'), (b'IAB2-6', b'Convertible'), (b'IAB2-9', b'Diesel'), (b'IAB2-8', b'Crossover'), (b'IAB9-18', b'Investors & Patents'), (b'IAB13-6', b'Insurance'), (b'IAB13-7', b'Investing'), (b'IAB13-4', b'Financial Planning'), (b'IAB13-5', b'Hedge Fund'), (b'IAB13-2', b'Credit/Debt & Loans'), (b'IAB13-3', b'Financial News'), (b'IAB2-13', b'Luxury'), (b'IAB13-1', b'Beginning Investing'), (b'IAB3-12', b'Metals'), (b'IAB3-10', b'Logistics'), (b'IAB3-11', b'Marketing'), (b'IAB2-19', b'Road-Side Assistance'), (b'IAB2-18', b'Pickup'), (b'IAB13-8', b'Mutual Funds'), (b'IAB13-9', b'Options'), (b'IAB19-24', b'Net for Beginners'), (b'IAB9-19', b'Jewelry Making'), (b'IAB17-43', b'Waterski/Wakeboard'), (b'IAB17-42', b'Walking'), (b'IAB17-41', b'Volleyball'), (b'IAB17-40', b'Tennis'), (b'IAB17-44', b'World Soccer'), (b'IAB11-1', b'Immigration'), (b'IAB11-2', b'Legal Issues'), (b'IAB11-3', b'U.S. Government Resources'), (b'IAB11-4', b'Politics'), (b'IAB11-5', b'Commentary'), (b'IAB7-27', b"IBS/Crohn's Disease"), (b'IAB7-26', b'Holistic Healing'), (b'IAB7-25', b'Herbs for Health'), (b'IAB7-24', b'Heart Disease'), (b'IAB7-23', b'Headaches/Migraines'), (b'IAB7-22', b'GERD/Acid Reflux'), (b'IAB7-21', b'Epilepsy'), (b'IAB7-20', b'Diabetes'), (b'IAB7-29', b'Incontinence'), (b'IAB7-28', b'Incest/Abuse Support'), (b'IAB20-16', b'Greece'), (b'IAB20-17', b'Honeymoons/Getaways'), (b'IAB20-14', b'Europe'), (b'IAB20-15', b'France'), (b'IAB20-12', b'Cruises'), (b'IAB20-13', b'Eastern Europe'), (b'IAB20-10', b'Canada'), (b'IAB20-11', b'Caribbean'), (b'IAB20-18', b'Hotels'), (b'IAB20-19', b'Italy'), (b'IAB19-10', b'Computer Reviews'), (b'IAB19-11', b'Data Centers'), (b'IAB21-3', b'Buying/Selling Homes'), (b'IAB9-16', b'Guitar'), (b'IAB21-2', b'Architects'), (b'IAB9-14', b'Genealogy'), (b'IAB18-1', b'Beauty'), (b'IAB18-3', b'Fashion'), (b'IAB18-2', b'Body Art'), (b'IAB18-5', b'Clothing'), (b'IAB9-15', b'Getting Published'), (b'IAB18-4', b'Jewelry'), (b'IAB6-9', b'Eldercare'), (b'IAB18-6', b'Accessories'), (b'IAB6-8', b'Special Needs Kids'), (b'IAB5-10', b'Homeschooling'), (b'IAB5-11', b'Homework/Study Tips'), (b'IAB5-12', b'K-6 Educators'), (b'IAB5-13', b'Private School'), (b'IAB5-14', b'Special Education'), (b'IAB5-15', b'Studying Business'), (b'IAB17-25', b'Power & Motorcycles'), (b'IAB6-4', b'Family Internet'), (b'IAB17-27', b'Pro Ice Hockey'), (b'IAB19-27', b'PC Support'), (b'IAB19-26', b'Palmtops/PDAs'), (b'IAB19-25', b'Network Security'), (b'IAB17-26', b'Pro Basketball'), (b'IAB19-23', b'Net Conferencing'), (b'IAB19-22', b'MP3/MIDI'), (b'IAB19-21', b'Mac Support'), (b'IAB19-20', b'JavaScript'), (b'IAB9-17', b'Home Recording'), (b'IAB17-21', b'Mountain Biking'), (b'IAB2-16', b'Off-Road Vehicles'), (b'IAB19-29', b'Entertainment'), (b'IAB19-28', b'Portable'), (b'IAB17-23', b'Olympics'), (b'IAB8-13', b'Italian Cuisine'), (b'IAB8-18', b'Wine'), (b'IAB9-10', b'Collecting'), (b'IAB8-6', b'Coffee/Tea'), (b'IAB2-11', b'Hatchback'), (b'IAB8-5', b'Cocktails/Beer'), (b'IAB8-4', b'Chinese Cuisine'), (b'IAB8-12', b'Health/Lowfat Cooking'), (b'IAB8-3', b'Cajun/Creole'), (b'IAB8-2', b'Barbecues & Grilling'), (b'IAB18', b'Style & Fashion'), (b'IAB19', b'Technology & Computing'), (b'IAB9-11', b'Comic Books'), (b'IAB8-1', b'American Cuisine'), (b'IAB2-10', b'Electric Vehicle'), (b'IAB13', b'Personal Finance'), (b'IAB10', b'Home & Garden'), (b'IAB11', b"Law, Gov't & Politics"), (b'IAB16', b'Pets'), (b'IAB17', b'Sports'), (b'IAB14', b'Society'), (b'IAB15', b'Science'), (b'IAB22-2', b'Couponing'), (b'IAB22-3', b'Comparison'), (b'IAB9-12', b'Drawing/Sketching'), (b'IAB6-2', b'Babies & Toddlers'), (b'IAB23-10', b'Pagan/Wiccan'), (b'IAB8-9', b'Dining Out'), (b'IAB9-13', b'Freelance Writing'), (b'IAB2-12', b'Hybrid'), (b'IAB17-6', b'Canoeing/Kayaking'), (b'IAB17-7', b'Cheerleading'), (b'IAB17-8', b'Climbing'), (b'IAB8-17', b'Vegetarian'), (b'IAB8-16', b'Vegan'), (b'IAB8-15', b'Mexican Cuisine'), (b'IAB8-14', b'Japanese Cuisine'), (b'IAB17-29', b'Rugby'), (b'IAB17-28', b'Rodeo'), (b'IAB8-11', b'French Cuisine'), (b'IAB8-10', b'Food Allergies'), (b'IAB6-5', b'Parenting - K-6 Kids'), (b'IAB17-24', b'Paintball'), (b'IAB6-7', b'Pregnancy'), (b'IAB6-6', b'Parenting teens'), (b'IAB6-1', b'Adoption'), (b'IAB17-20', b'Martial Arts'), (b'IAB6-3', b'Daycare/Pre School'), (b'IAB17-22', b'NASCAR Racing'), (b'IAB17-9', b'Cricket'), (b'IAB7-45', b"Women's Health"), (b'IAB7-44', b'Weight Loss'), (b'IAB7-41', b'Smoking Cessation'), (b'IAB7-40', b'Sleep Disorders'), (b'IAB7-43', b'Thyroid Disease'), (b'IAB7-42', b'Substance Abuse'), (b'IAB25', b'Non-Standard Content'), (b'IAB12', b'News'), (b'IAB24', b'Uncategorized'), (b'IAB22', b'Shopping'), (b'IAB21', b'Real Estate'), (b'IAB15-3', b'Chemistry'), (b'IAB2-20', b'Sedan'), (b'IAB2-21', b'Trucks & Accessories'), (b'IAB2-22', b'Vintage Cars'), (b'IAB2-23', b'Wagon'), (b'IAB26-2', b'Warez'), (b'IAB26-3', b'Spyware/Malware'), (b'IAB4-9', b'Telecommuting'), (b'IAB4-8', b'Scholarships'), (b'IAB4-3', b'Financial Aid'), (b'IAB4-2', b'College'), (b'IAB4-1', b'Career Planning'), (b'IAB4-7', b'Nursing'), (b'IAB4-6', b'Resume Writing/Advice'), (b'IAB4-5', b'Job Search'), (b'IAB4-4', b'Job Fairs'), (b'IAB20-23', b'South America'), (b'IAB20-22', b'National Parks'), (b'IAB20-21', b'Mexico & Central America'), (b'IAB20-20', b'Japan'), (b'IAB20-27', b'United Kingdom'), (b'IAB20-26', b'Traveling with Kids'), (b'IAB20-25', b'Theme Parks'), (b'IAB20-24', b'Spas'), (b'IAB23-3', b'Buddhism'), (b'IAB23-2', b'Atheism/Agnosticism'), (b'IAB23-1', b'Alternative Religions'), (b'IAB23-7', b'Islam'), (b'IAB23-6', b'Hinduism'), (b'IAB23-5', b'Christianity'), (b'IAB23-4', b'Catholicism'), (b'IAB23-9', b'Latter-Day Saints'), (b'IAB23-8', b'Judaism'), (b'IAB7-34', b'Panic/Anxiety Disorders'), (b'IAB21-1', b'Apartments'), (b'IAB9-8', b'Chess'), (b'IAB9-9', b'Cigars'), (b'IAB9-6', b'Candle & Soap Making'), (b'IAB9-7', b'Card Games'), (b'IAB9-4', b'Birdwatching'), (b'IAB9-5', b'Board Games/Puzzles'), (b'IAB9-2', b'Arts & Crafts'), (b'IAB9-3', b'Beadwork'), (b'IAB9-1', b'Art/Technology'), (b'IAB16-3', b'Cats'), (b'IAB16-2', b'Birds'), (b'IAB16-1', b'Aquariums'), (b'IAB16-7', b'Veterinary Medicine'), (b'IAB16-6', b'Reptiles'), (b'IAB16-5', b'Large Animals'), (b'IAB16-4', b'Dogs'), (b'IAB7-32', b'Nutrition'), (b'IAB7-33', b'Orthopedics'), (b'IAB1', b'Arts & Entertainment'), (b'IAB2', b'Automotive'), (b'IAB3', b'Business'), (b'IAB4', b'Careers'), (b'IAB5', b'Education'), (b'IAB6', b'Family & Parenting'), (b'IAB7', b'Health & Fitness'), (b'IAB8', b'Food & Drink'), (b'IAB9', b'Hobbies & Interests'), (b'IAB7-38', b'Senor Health'), (b'IAB7-39', b'Sexuality'), (b'IAB3-8', b'Green Solutions'), (b'IAB3-9', b'Human Resources'), (b'IAB7-36', b'Physical Therapy'), (b'IAB7-37', b'Psychology/Psychiatry'), (b'IAB7-30', b'Infertility'), (b'IAB7-31', b"Men's Health"), (b'IAB9-30', b'Video & Computer Games'), (b'IAB9-31', b'Woodworking'), (b'IAB3-1', b'Advertising'), (b'IAB3-2', b'Agriculture'), (b'IAB3-3', b'Biotech/Biomedical'), (b'IAB3-4', b'Business Software'), (b'IAB3-5', b'Construction'), (b'IAB3-6', b'Forestry'), (b'IAB3-7', b'Government')])),
                ('promotion_goal', models.IntegerField(default=1, choices=[(3, b'Conversions'), (1, b'Brand Building'), (2, b'Traffic Acquisition')])),
                ('campaign_goal', models.IntegerField(default=3, choices=[(5, b'pages per session'), (2, b'% bounce rate'), (3, b'new unique visitors'), (1, b'CPA'), (4, b'seconds time on site')])),
                ('goal_quantity', models.DecimalField(default=0, max_digits=20, decimal_places=2)),
                ('target_devices', jsonfield.fields.JSONField(default=[], blank=True)),
                ('target_regions', jsonfield.fields.JSONField(default=[], blank=True)),
                ('archived', models.BooleanField(default=False)),
                ('changes_text', models.TextField(null=True, blank=True)),
                ('account_manager', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True)),
                ('campaign', models.ForeignKey(related_name='settings', on_delete=django.db.models.deletion.PROTECT, to='dash.Campaign')),
                ('created_by', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('sales_representative', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-created_dt',),
            },
        ),
        migrations.CreateModel(
            name='ContentAd',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.CharField(max_length=2048, editable=False)),
                ('title', models.CharField(max_length=256, editable=False)),
                ('display_url', models.CharField(default=b'', max_length=25, blank=True)),
                ('brand_name', models.CharField(default=b'', max_length=25, blank=True)),
                ('description', models.CharField(default=b'', max_length=140, blank=True)),
                ('call_to_action', models.CharField(default=b'', max_length=25, blank=True)),
                ('image_id', models.CharField(max_length=256, null=True, editable=False)),
                ('image_width', models.PositiveIntegerField(null=True)),
                ('image_height', models.PositiveIntegerField(null=True)),
                ('image_hash', models.CharField(max_length=128, null=True)),
                ('crop_areas', models.CharField(max_length=128, null=True)),
                ('redirect_id', models.CharField(max_length=128, null=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('state', models.IntegerField(default=1, null=True, choices=[(1, b'Enabled'), (2, b'Paused')])),
                ('archived', models.BooleanField(default=False)),
                ('tracker_urls', django.contrib.postgres.fields.ArrayField(null=True, base_field=models.CharField(max_length=2048), size=None)),
                ('ad_group', models.ForeignKey(to='dash.AdGroup', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'get_latest_by': 'created_dt',
            },
        ),
        migrations.CreateModel(
            name='ContentAdSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('submission_status', models.IntegerField(default=-1, choices=[(1, b'Pending'), (4, b'Limit reached'), (-1, b'Not submitted'), (2, b'Approved'), (3, b'Rejected')])),
                ('submission_errors', models.TextField(null=True, blank=True)),
                ('state', models.IntegerField(default=2, null=True, choices=[(1, b'Enabled'), (2, b'Paused')])),
                ('source_state', models.IntegerField(default=2, null=True, choices=[(1, b'Enabled'), (2, b'Paused')])),
                ('source_content_ad_id', models.CharField(max_length=50, null=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('content_ad', models.ForeignKey(to='dash.ContentAd', on_delete=django.db.models.deletion.PROTECT)),
            ],
        ),
        migrations.CreateModel(
            name='ConversionGoal',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.PositiveSmallIntegerField(choices=[(1, b'Conversion Pixel'), (3, b'Adobe Analytics'), (2, b'Google Analytics')])),
                ('name', models.CharField(max_length=100)),
                ('conversion_window', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('goal_id', models.CharField(max_length=100, null=True, blank=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created on')),
                ('campaign', models.ForeignKey(to='dash.Campaign', on_delete=django.db.models.deletion.PROTECT)),
            ],
        ),
        migrations.CreateModel(
            name='ConversionPixel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.CharField(max_length=32)),
                ('archived', models.BooleanField(default=False)),
                ('last_sync_dt', models.DateTimeField(default=datetime.datetime.utcnow, null=True, blank=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created on')),
                ('account', models.ForeignKey(to='dash.Account', on_delete=django.db.models.deletion.PROTECT)),
            ],
        ),
        migrations.CreateModel(
            name='CreditHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('snapshot', jsonfield.fields.JSONField()),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('created_by', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CreditLineItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('amount', models.IntegerField()),
                ('license_fee', models.DecimalField(default=Decimal('0.2000'), max_digits=5, decimal_places=4)),
                ('status', models.IntegerField(default=2, choices=[(1, b'Signed'), (3, b'Canceled'), (2, b'Pending')])),
                ('comment', models.CharField(max_length=256, null=True, blank=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('account', models.ForeignKey(related_name='credits', on_delete=django.db.models.deletion.PROTECT, to='dash.Account')),
                ('created_by', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, verbose_name=b'Created by', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DefaultSourceSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('params', jsonfield.fields.JSONField(default={}, help_text=b'Information about format can be found here: <a href="https://sites.google.com/a/zemanta.com/root/content-ads-dsp/additional-source-parameters-format" target="_blank">Zemanta Pages</a>', verbose_name=b'Additional action parameters', blank=True)),
                ('default_cpc_cc', models.DecimalField(null=True, verbose_name=b'Default CPC', max_digits=10, decimal_places=4, blank=True)),
                ('mobile_cpc_cc', models.DecimalField(null=True, verbose_name=b'Default CPC (if ad group is targeting mobile only)', max_digits=10, decimal_places=4, blank=True)),
                ('daily_budget_cc', models.DecimalField(null=True, verbose_name=b'Default daily budget', max_digits=10, decimal_places=4, blank=True)),
                ('auto_add', models.BooleanField(default=False, verbose_name=b'Automatically add this source to ad group at creation')),
            ],
            options={
                'verbose_name_plural': 'Default Source Settings',
            },
        ),
        migrations.CreateModel(
            name='DemoAdGroupRealAdGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('multiplication_factor', models.IntegerField(default=1)),
                ('demo_ad_group', models.OneToOneField(related_name='+', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroup')),
                ('real_ad_group', models.OneToOneField(related_name='+', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroup')),
            ],
        ),
        migrations.CreateModel(
            name='ExportReport',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('granularity', models.IntegerField(default=5, choices=[(5, b'Content Ad'), (4, b'Ad Group'), (3, b'Campaign'), (1, b'All Accounts'), (2, b'Account')])),
                ('breakdown_by_day', models.BooleanField(default=False)),
                ('breakdown_by_source', models.BooleanField(default=False)),
                ('order_by', models.CharField(max_length=20, null=True, blank=True)),
                ('additional_fields', models.CharField(max_length=500, null=True, blank=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.Account', null=True)),
                ('ad_group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.AdGroup', null=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.Campaign', null=True)),
                ('created_by', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='OutbrainAccount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('marketer_id', models.CharField(max_length=255)),
                ('used', models.BooleanField(default=False)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
            ],
        ),
        migrations.CreateModel(
            name='PublisherBlacklist',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=127, verbose_name=b'Publisher name')),
                ('everywhere', models.BooleanField(default=False, verbose_name=b'globally blacklisted')),
                ('status', models.IntegerField(default=2, choices=[(2, b'Blacklisted'), (1, b'Enabled'), (3, b'Pending')])),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('account', models.ForeignKey(related_name='account', on_delete=django.db.models.deletion.PROTECT, to='dash.Account', null=True)),
                ('ad_group', models.ForeignKey(related_name='ad_group', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroup', null=True)),
                ('campaign', models.ForeignKey(related_name='campaign', on_delete=django.db.models.deletion.PROTECT, to='dash.Campaign', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ScheduledExportReport',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100, null=True, blank=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('state', models.IntegerField(default=1, choices=[(2, b'Paused'), (1, b'Enabled'), (3, b'Removed')])),
                ('sending_frequency', models.IntegerField(default=1, choices=[(3, b'Monthly'), (1, b'Daily'), (2, b'Weekly')])),
                ('created_by', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('report', models.ForeignKey(related_name='scheduled_reports', to='dash.ExportReport')),
            ],
        ),
        migrations.CreateModel(
            name='ScheduledExportReportLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('start_date', models.DateField(null=True)),
                ('end_date', models.DateField(null=True)),
                ('report_filename', models.CharField(max_length=1024, null=True)),
                ('recipient_emails', models.CharField(max_length=1024, null=True)),
                ('state', models.IntegerField(default=2, choices=[(2, b'Failed'), (1, b'Success')])),
                ('errors', models.TextField(null=True)),
                ('scheduled_report', models.ForeignKey(to='dash.ScheduledExportReport')),
            ],
        ),
        migrations.CreateModel(
            name='ScheduledExportReportRecipient',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=254)),
                ('scheduled_report', models.ForeignKey(related_name='recipients', to='dash.ScheduledExportReport')),
            ],
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=127)),
                ('tracking_slug', models.CharField(unique=True, max_length=50, verbose_name=b'Tracking slug')),
                ('bidder_slug', models.CharField(max_length=50, unique=True, null=True, verbose_name=b'B1 Slug', blank=True)),
                ('maintenance', models.BooleanField(default=True)),
                ('deprecated', models.BooleanField(default=False)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('released', models.BooleanField(default=True)),
                ('content_ad_submission_type', models.IntegerField(default=1, choices=[(1, b'Default'), (3, b'Submit whole batch at once'), (2, b'One submission per ad group')])),
            ],
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
                'verbose_name_plural': 'Source Credentials',
            },
        ),
        migrations.CreateModel(
            name='SourceType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(unique=True, max_length=127)),
                ('available_actions', django.contrib.postgres.fields.ArrayField(size=None, null=True, base_field=models.PositiveSmallIntegerField(), blank=True)),
                ('min_cpc', models.DecimalField(null=True, verbose_name=b'Minimum CPC', max_digits=10, decimal_places=4, blank=True)),
                ('min_daily_budget', models.DecimalField(null=True, verbose_name=b'Minimum Daily Budget', max_digits=10, decimal_places=4, blank=True)),
                ('max_cpc', models.DecimalField(null=True, verbose_name=b'Maximum CPC', max_digits=10, decimal_places=4, blank=True)),
                ('max_daily_budget', models.DecimalField(null=True, verbose_name=b'Maximum Daily Budget', max_digits=10, decimal_places=4, blank=True)),
                ('cpc_decimal_places', models.PositiveSmallIntegerField(null=True, verbose_name=b'CPC Decimal Places', blank=True)),
                ('delete_traffic_metrics_threshold', models.IntegerField(default=0, help_text=b"When we receive an empty report, we don't override existing data but we mark report aggregation as failed. But for smaller changes (as defined by this parameter), we do override existing data since they are not material. Zero value means no reports will get deleted.", verbose_name=b'Max clicks allowed to delete per daily report')),
            ],
            options={
                'verbose_name': 'Source Type',
                'verbose_name_plural': 'Source Types',
            },
        ),
        migrations.CreateModel(
            name='UploadBatch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=1024)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('status', models.IntegerField(default=3, choices=[(2, b'Failed'), (1, b'Done'), (3, b'In progress')])),
                ('error_report_key', models.CharField(max_length=1024, null=True, blank=True)),
                ('num_errors', models.PositiveIntegerField(null=True)),
                ('processed_content_ads', models.PositiveIntegerField(null=True)),
                ('inserted_content_ads', models.PositiveIntegerField(null=True)),
                ('batch_size', models.PositiveIntegerField(null=True)),
            ],
            options={
                'get_latest_by': 'created_dt',
            },
        ),
        migrations.CreateModel(
            name='UserActionLog',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('action_type', models.PositiveSmallIntegerField(choices=[(1, b'Upload Content Ads'), (14, b'Set Campaign Budget'), (7, b'Archive/Restore Ad Group'), (10, b'Archive/Restore Account'), (3, b'Archive/Restore Content Ad(s)'), (16, b'Create Conversion Goal'), (2, b'Set Content Ad(s) State'), (19, b'Archive/Restore Conversion Pixel'), (21, b'Set Media Source Settings'), (15, b'Archive/Restore Campaign'), (18, b'Create Conversion Pixel'), (20, b'Create Media Source Campaign'), (5, b'Set Ad Group Settings'), (11, b'Create Campaign'), (17, b'Delete Conversion Goal'), (9, b'Set Account Agency Settings'), (12, b'Set Campaign Settings'), (13, b'Set Campaign Agency Settings'), (6, b'Set Ad Group Settings (with auto added Media Sources)'), (8, b'Create Account'), (4, b'Create Ad Group')])),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.Account', null=True)),
                ('account_settings', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.AccountSettings', null=True)),
                ('ad_group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.AdGroup', null=True)),
                ('ad_group_settings', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.AdGroupSettings', null=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.Campaign', null=True)),
                ('campaign_settings', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.CampaignSettings', null=True)),
                ('created_by', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='source',
            name='source_type',
            field=models.ForeignKey(to='dash.SourceType', null=True),
        ),
        migrations.AddField(
            model_name='publisherblacklist',
            name='source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dash.Source', null=True),
        ),
        migrations.AddField(
            model_name='exportreport',
            name='filtered_sources',
            field=models.ManyToManyField(to='dash.Source', blank=True),
        ),
        migrations.AddField(
            model_name='defaultsourcesettings',
            name='credentials',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.SourceCredentials', null=True),
        ),
        migrations.AddField(
            model_name='defaultsourcesettings',
            name='source',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='dash.Source'),
        ),
        migrations.AddField(
            model_name='credithistory',
            name='credit',
            field=models.ForeignKey(related_name='history', to='dash.CreditLineItem'),
        ),
        migrations.AddField(
            model_name='conversiongoal',
            name='pixel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dash.ConversionPixel', null=True),
        ),
        migrations.AddField(
            model_name='contentadsource',
            name='source',
            field=models.ForeignKey(to='dash.Source', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AddField(
            model_name='contentad',
            name='batch',
            field=models.ForeignKey(to='dash.UploadBatch', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AddField(
            model_name='contentad',
            name='sources',
            field=models.ManyToManyField(to='dash.Source', through='dash.ContentAdSource'),
        ),
        migrations.AddField(
            model_name='budgetlineitem',
            name='campaign',
            field=models.ForeignKey(related_name='budgets', on_delete=django.db.models.deletion.PROTECT, to='dash.Campaign'),
        ),
        migrations.AddField(
            model_name='budgetlineitem',
            name='created_by',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, verbose_name=b'Created by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='budgetlineitem',
            name='credit',
            field=models.ForeignKey(related_name='budgets', on_delete=django.db.models.deletion.PROTECT, to='dash.CreditLineItem'),
        ),
        migrations.AddField(
            model_name='budgethistory',
            name='budget',
            field=models.ForeignKey(related_name='history', to='dash.BudgetLineItem'),
        ),
        migrations.AddField(
            model_name='budgethistory',
            name='created_by',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='adgroupsource',
            name='source',
            field=models.ForeignKey(to='dash.Source', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AddField(
            model_name='adgroupsource',
            name='source_credentials',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dash.SourceCredentials', null=True),
        ),
        migrations.AddField(
            model_name='adgroup',
            name='campaign',
            field=models.ForeignKey(to='dash.Campaign', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AddField(
            model_name='adgroup',
            name='modified_by',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='adgroup',
            name='sources',
            field=models.ManyToManyField(to='dash.Source', through='dash.AdGroupSource'),
        ),
        migrations.AlterUniqueTogether(
            name='scheduledexportreportrecipient',
            unique_together=set([('scheduled_report', 'email')]),
        ),
        migrations.AlterUniqueTogether(
            name='publisherblacklist',
            unique_together=set([('name', 'everywhere', 'account', 'campaign', 'ad_group', 'source')]),
        ),
        migrations.AlterUniqueTogether(
            name='conversionpixel',
            unique_together=set([('slug', 'account')]),
        ),
        migrations.AlterUniqueTogether(
            name='conversiongoal',
            unique_together=set([('campaign', 'type', 'goal_id'), ('campaign', 'pixel'), ('campaign', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='article',
            unique_together=set([('ad_group', 'url', 'title')]),
        ),
    ]
