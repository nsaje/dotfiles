import mock
from decimal import Decimal
import datetime

from django.test import TestCase

from utils.magic_mixer import magic_mixer
import dash.models
import dash.constants

import service


class TestService(TestCase):

    @mock.patch('utils.dates_helper.local_today', return_value=datetime.date(2017, 1, 1))
    @mock.patch('dash.features.contentupload.upload.persist_batch', autospec=True)
    @mock.patch('automation.autopilot_plus.initialize_budget_autopilot_on_ad_group', autospec=True)
    @mock.patch('utils.redirector_helper.insert_adgroup', autospec=True)
    @mock.patch('utils.k1_helper.update_ad_group', autospec=True)
    def test_launch(self, mock_k1_update, mock_redirector_insert, mock_autopilot, mock_persist_batch, mock_local_today):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(dash.models.Account)
        credit = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=account,
            start_date=datetime.date(2017, 1, 1),
            end_date=datetime.date(2017, 3, 3),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=500
        )
        pixel = magic_mixer.blend(dash.models.ConversionPixel, account=account)
        upload_batch = magic_mixer.blend(dash.models.UploadBatch, account=account)

        campaign = service.launch(
            request=request,
            account=account,
            name='xyz',
            iab_category=dash.constants.IABCategory.IAB1_1,
            language=dash.constants.Language.SPANISH,
            budget_amount=234,
            upload_batch=upload_batch,
            goal_type=dash.constants.CampaignGoalKPI.CPA,
            goal_value=Decimal(30.0),
            max_cpc=Decimal('0.5'),
            daily_budget=Decimal('15.2'),
            target_regions=['US'],
            exclusion_target_regions=['US-NY'],
            target_devices=[dash.constants.AdTargetDevice.DESKTOP],
            target_placements=[dash.constants.Placement.APP],
            target_os=[{'name': dash.constants.OperatingSystem.ANDROID}],
            conversion_goal_type=dash.constants.ConversionGoalType.PIXEL,
            conversion_goal_goal_id=str(pixel.id),
            conversion_goal_window=dash.constants.ConversionWindows.LEQ_1_DAY
        )

        campaign_settings = campaign.get_current_settings()
        self.assertEqual(campaign_settings.name, 'xyz')
        self.assertEqual(campaign_settings.iab_category, dash.constants.IABCategory.IAB1_1)
        self.assertEqual(campaign_settings.language, dash.constants.Language.SPANISH)

        budget = campaign.budgets.first()
        self.assertEqual(budget, credit.budgets.first())
        self.assertEqual(budget.start_date, datetime.date(2017, 1, 1))
        self.assertEqual(budget.end_date, datetime.date(2017, 3, 3))
        self.assertEqual(budget.amount, 234)

        goal = campaign.campaigngoal_set.first()
        self.assertEqual(goal.type, dash.constants.CampaignGoalKPI.CPA)
        self.assertEqual(goal.conversion_goal.type, dash.constants.ConversionGoalType.PIXEL)

        ad_group = campaign.adgroup_set.first()
        self.assertEqual(ad_group.settings.start_date, datetime.date(2017, 1, 1))
        self.assertEqual(ad_group.settings.end_date, None)
        self.assertEqual(ad_group.settings.cpc_cc, Decimal('0.5'))
        self.assertEqual(ad_group.settings.daily_budget_cc, Decimal('15.2'))
        self.assertEqual(ad_group.settings.autopilot_daily_budget, Decimal('15.2'))
        self.assertEqual(ad_group.settings.target_regions, ['US'])
        self.assertEqual(ad_group.settings.exclusion_target_regions, ['US-NY'])
        self.assertEqual(ad_group.settings.target_devices, [dash.constants.AdTargetDevice.DESKTOP])
        self.assertEqual(ad_group.settings.target_placements, [dash.constants.Placement.APP])
        self.assertEqual(ad_group.settings.target_os, [{'name': dash.constants.OperatingSystem.ANDROID}])

        self.assertEqual(upload_batch.ad_group, ad_group)
        mock_persist_batch.assert_called_with(upload_batch)
