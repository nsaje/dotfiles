from django.test import TestCase

from dash.views import helpers
from dash import models


class ViewHelpersTestCase(TestCase):
    fixtures = ['test_api.yaml']

    def test_get_ad_group_sources_data_status_messages(self):
        ad_group_source1 = models.AdGroupSource.objects.get(pk=1)
        ad_group_source2 = models.AdGroupSource.objects.get(pk=2)
        ad_group_source3 = models.AdGroupSource.objects.get(pk=3)

        data_status = helpers.get_ad_group_sources_data_status(
            [ad_group_source1, ad_group_source2, ad_group_source3])

        self.assertEqual(
            data_status[ad_group_source1.source_id]['message'],
            '<b>Status</b> for this Media Source differs from Status in the Media Source\'s 3rd party dashboard.'
        )

        self.assertEqual(
            data_status[ad_group_source2.source_id]['message'],
            '<b>Bid CPC</b> for this Media Source differs from Bid CPC in the Media Source\'s 3rd party dashboard.<br/><b>Daily Budget</b> for this Media Source differs from Daily Budget in the Media Source\'s 3rd party dashboard.'
        )

        self.assertEqual(
            data_status[ad_group_source3.source_id]['message'],
            'Everything is OK. Last OK sync was on: <b>06/10/2014 5:58 AM</b>'
        )
