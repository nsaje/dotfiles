import decimal
from django.test import TestCase
from mock import patch

from utils.magic_mixer import magic_mixer
import core.entity
import dash.constants

from . import service


class TestGoalsService(TestCase):

    @patch.object(core.multicurrency, 'get_current_exchange_rate')
    def test_get_campaign_goals_defaults(self, mock_get_exchange_rate):
        mock_get_exchange_rate.return_value = decimal.Decimal('2.0')
        account = magic_mixer.blend(core.entity.Account)

        self.assertEqual(
            service.get_campaign_goals_defaults(account),
            {
                dash.constants.CampaignGoalKPI.TIME_ON_SITE: '30.00',
                dash.constants.CampaignGoalKPI.MAX_BOUNCE_RATE: '75.00',
                dash.constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS: '85.00',
                dash.constants.CampaignGoalKPI.PAGES_PER_SESSION: '1.20',
                dash.constants.CampaignGoalKPI.CPA: '100.00',
                dash.constants.CampaignGoalKPI.CPC: '0.700',
                dash.constants.CampaignGoalKPI.CPV: '1.00',
                dash.constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT: '5.60',
                dash.constants.CampaignGoalKPI.CP_NEW_VISITOR: '5.60',
                dash.constants.CampaignGoalKPI.CP_PAGE_VIEW: '0.90',
                dash.constants.CampaignGoalKPI.CPCV: '1.20',
            }
        )
