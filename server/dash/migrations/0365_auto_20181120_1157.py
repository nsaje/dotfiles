# Generated by Django 2.1.2 on 2018-11-20 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("dash", "0364_cpm_buying_ags_local_cpm_backfill")]

    operations = [
        migrations.AddField(model_name="source", name="cpc_billing", field=models.BooleanField(default=False)),
        migrations.AlterField(
            model_name="emailtemplate",
            name="template_type",
            field=models.PositiveSmallIntegerField(
                blank=True,
                choices=[
                    (1, "Ad group settings change"),
                    (2, "Campaign settings change"),
                    (3, "Budget change"),
                    (4, "New conversion pixel"),
                    (5, "User password reset"),
                    (6, "New user introduction email"),
                    (7, "Supply report"),
                    (8, "Scheduled report"),
                    (9, "Depleting budget notification"),
                    (10, "Campaign stopped notification"),
                    (11, "Autopilot changes notification"),
                    (12, "Autopilot initialisation notification"),
                    (15, "Demo is running"),
                    (16, "Livestream sesion id"),
                    (17, "Daily management report"),
                    (18, "Unused Outbrain accounts running out"),
                    (19, "Google Analytics Setup Instructions"),
                    (20, "Report results"),
                    (21, "Depleting credits"),
                    (22, "Account settings change"),
                    (23, "Weekly client report"),
                    (24, "Pacing notification"),
                    (25, "Weekly inventory report"),
                    (26, "New device login"),
                    (27, "Scheduled report results"),
                    (28, "Zemanta OEN CPA Optimization Factors"),
                    (29, "Report fail"),
                    (30, "Campaign Autopilot changes notification"),
                    (31, "Campaign Autopilot initialisation notification"),
                    (32, "Real-time campaign stop budget depleting"),
                    (33, "User was granted REST API access"),
                    (34, "Campaign created"),
                ],
                null=True,
            ),
        ),
    ]