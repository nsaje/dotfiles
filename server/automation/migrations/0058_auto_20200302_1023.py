# Generated by Django 2.1.11 on 2020-03-02 10:23

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("automation", "0057_auto_20200219_1709")]

    operations = [
        migrations.AlterField(
            model_name="rulecondition",
            name="left_operand_type",
            field=models.IntegerField(
                choices=[
                    (1, "Total spend"),
                    (2, "Impressions"),
                    (3, "Clicks"),
                    (4, "CTR"),
                    (5, "Average CPC"),
                    (6, "Average CPM"),
                    (7, "Visits"),
                    (8, "New visits"),
                    (9, "Unique users"),
                    (10, "New users"),
                    (11, "Returning users"),
                    (12, "New users percentage"),
                    (13, "Click discrepancy"),
                    (14, "Pageviews"),
                    (15, "Pageviews per visit"),
                    (16, "Bounced visits"),
                    (17, "Non-bounced visits"),
                    (18, "Bounce rate"),
                    (19, "Total seconds"),
                    (20, "Average time on site"),
                    (21, "Average cost per visit"),
                    (22, "Average cost per new visitor"),
                    (23, "Average cost per pageview"),
                    (24, "Average cost per non-bounced visit"),
                    (25, "Average cost per minute"),
                    (26, "Video start"),
                    (27, "Video fist quartile"),
                    (28, "Video midpoint"),
                    (29, "Video third quartile"),
                    (30, "Video complete"),
                    (31, "Average CPV"),
                    (32, "Average CPCV"),
                    (33, "Account name"),
                    (34, "Account created date"),
                    (35, "Days since account created"),
                    (36, "Campaign name"),
                    (37, "Campaign created date"),
                    (38, "Days since campaign created"),
                    (39, "Campaign type"),
                    (40, "Campaign manager"),
                    (41, "Campaign category"),
                    (42, "Campaign language"),
                    (43, "Campaign primary goal"),
                    (44, "Campaign primary goal value"),
                    (45, "Ad group name"),
                    (46, "Ad group created date"),
                    (47, "Days since ad group created"),
                    (48, "Ad group start date"),
                    (49, "Ad group end date"),
                    (50, "Ad group bidding type"),
                    (51, "Ad group bid"),
                    (52, "Ad group daily cap"),
                    (53, "Ad group delivery type"),
                    (54, "Ad title"),
                    (55, "Ad label"),
                    (56, "Ad created date"),
                    (57, "Days since ad created"),
                ]
            ),
        ),
        migrations.AlterField(
            model_name="rulecondition",
            name="right_operand_type",
            field=models.IntegerField(
                choices=[
                    (1, "Absolute value"),
                    (2, "Constant"),
                    (3, "Current date"),
                    (4, "Account manager"),
                    (5, "Campaign goal"),
                    (6, "Campaign budget"),
                    (7, "Remaining campaign budget"),
                    (8, "Ad group bid"),
                    (9, "Ad group click daily cap"),
                    (10, "Daily cap"),
                    (11, "Daily cap spent ratio"),
                    (12, "Total spend"),
                    (13, "Total spend (daily average)"),
                ]
            ),
        ),
    ]
