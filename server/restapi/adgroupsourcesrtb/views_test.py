from decimal import Decimal
from django.core.urlresolvers import reverse

from restapi.views_test import RESTAPITest
from dash import constants
from core import source
import core.entity.adgroup


class AdGroupSourcesRTBTest(RESTAPITest):

    @classmethod
    def adgroupsourcertb_repr(
        cls,
        group_enabled=True,
        daily_budget=source.AllRTBSource.default_daily_budget_cc,
        state=constants.AdGroupSourceSettingsState.ACTIVE,
        cpc=source.AllRTBSource.default_cpc_cc,
    ):
        representation = {
            'groupEnabled': group_enabled,
            'dailyBudget': daily_budget,
            'state': constants.AdGroupSourceSettingsState.get_name(state),
            'cpc': cpc
        }
        return cls.normalize(representation)

    def validate_against_db(self, ad_group_id, agsrtb):
        settings_db = core.entity.adgroup.AdGroup.objects.get(pk=ad_group_id).get_current_settings()
        expected = self.adgroupsourcertb_repr(
            group_enabled=settings_db.b1_sources_group_enabled,
            daily_budget=settings_db.b1_sources_group_daily_budget.quantize(Decimal('1.00')),
            state=settings_db.b1_sources_group_state,
            cpc=settings_db.b1_sources_group_cpc_cc,
        )
        self.assertEqual(expected, agsrtb)

    def test_adgroups_sources_rtb_get(self):
        r = self.client.get(reverse('adgroups_sources_rtb_details', kwargs={'ad_group_id': 2040}))
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(2040, resp_json['data'])

    def test_adgroups_sources_rtb_put(self):
        test_rtbs = self.adgroupsourcertb_repr(
            group_enabled=True,
            daily_budget='12.38',
            state=constants.AdGroupSettingsState.ACTIVE,
            cpc='0.1230'
        )
        r = self.client.put(
            reverse('adgroups_sources_rtb_details', kwargs={'ad_group_id': 2040}),
            data=test_rtbs,
            format='json',
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(2040, resp_json['data'])
        self.assertEqual(test_rtbs, resp_json['data'])

    def test_adgroups_sources_rtb_put_default_values(self):
        test_rtbs = self.adgroupsourcertb_repr(
            group_enabled=True,
            state=constants.AdGroupSettingsState.ACTIVE,
        )
        r = self.client.put(
            reverse('adgroups_sources_rtb_details', kwargs={'ad_group_id': 2040}),
            data=test_rtbs,
            format='json',
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(2040, resp_json['data'])
        self.assertEqual(test_rtbs, resp_json['data'])
