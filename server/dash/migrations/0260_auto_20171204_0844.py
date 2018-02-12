# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-12-04 08:44


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0259_auto_20171124_1035'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubmissionFilter',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('state', models.IntegerField(choices=[(1, b'Block'), (2, b'Allow')], default=1)),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='submission_filters', to='dash.Account')),
                ('ad_group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='submission_filters', to='dash.AdGroup')),
                ('agency', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='submission_filters', to='dash.Agency')),
                ('campaign', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='submission_filters', to='dash.Campaign')),
                ('content_ad', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='submission_filters', to='dash.ContentAd')),
            ],
        ),
        migrations.AddField(
            model_name='source',
            name='content_ad_submission_policy',
            field=models.IntegerField(choices=[(1, b'Automatic'), (2, b'Manual')], default=1, help_text='Designates weather content ads are submitted automatically'),
        ),
        migrations.AddField(
            model_name='submissionfilter',
            name='source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='submission_filters', to='dash.Source'),
        ),
    ]
