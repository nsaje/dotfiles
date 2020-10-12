# Generated by Django 2.1.11 on 2020-10-07 16:02

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("dash", "0488_auto_20201006_0821")]

    operations = [
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
                    (35, "Automation rule run"),
                    (36, "Automation rule run without changes"),
                    (37, "Automation rule run with errors"),
                    (38, "Campaign cloned successfully"),
                    (39, "Campaign cloned error"),
                    (40, "Ad group cloned successfully"),
                    (41, "Ad group cloned error"),
                ],
                null=True,
            ),
        )
    ]
