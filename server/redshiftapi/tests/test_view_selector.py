from django.test import TestCase

from redshiftapi import view_selector


class ViewSelectorTest(TestCase):
    def test_get_best_view_base(self):
        self.assertEqual(view_selector.get_best_view_base(['account_id', 'month']), 'mv_account')
        self.assertEqual(view_selector.get_best_view_base(['account_id', 'source_id']), 'mv_account')
        self.assertEqual(view_selector.get_best_view_base(['account_id', 'source_id', 'age']), 'mv_account_delivery_demo')  # noqa
        self.assertEqual(view_selector.get_best_view_base(['account_id', 'source_id', 'dma']), 'mv_account_delivery_geo')  # noqa
        self.assertEqual(view_selector.get_best_view_base(['account_id', 'campaign_id']), 'mv_campaign')
        self.assertEqual(view_selector.get_best_view_base(['account_id', 'ad_group_id']), 'mv_ad_group')

        self.assertEqual(view_selector.get_best_view_base(['campaign_id', 'month']), 'mv_campaign')
        self.assertEqual(view_selector.get_best_view_base(['campaign_id', 'source_id']), 'mv_campaign')
        self.assertEqual(view_selector.get_best_view_base(['campaign_id', 'source_id', 'age']), 'mv_campaign_delivery_demo')  # noqa
        self.assertEqual(view_selector.get_best_view_base(['campaign_id', 'source_id', 'dma']), 'mv_campaign_delivery_geo')  # noqa
        self.assertEqual(view_selector.get_best_view_base(['campaign_id', 'ad_group_id']), 'mv_ad_group')
        self.assertEqual(view_selector.get_best_view_base(['campaign_id', 'content_ad_id']), 'mv_content_ad')

        self.assertEqual(view_selector.get_best_view_base(['ad_group_id', 'month']), 'mv_ad_group')
        self.assertEqual(view_selector.get_best_view_base(['ad_group_id', 'source_id']), 'mv_ad_group')
        self.assertEqual(view_selector.get_best_view_base(['ad_group_id', 'source_id', 'age']), 'mv_ad_group_delivery_demo')  # noqa
        self.assertEqual(view_selector.get_best_view_base(['ad_group_id', 'source_id', 'dma']), 'mv_ad_group_delivery_geo')  # noqa
        self.assertEqual(view_selector.get_best_view_base(['ad_group_id', 'content_ad_id']), 'mv_content_ad')

        self.assertEqual(view_selector.get_best_view_base(['ad_group_id', 'publisher_id'], True), 'mv_pubs_ad_group')
        self.assertEqual(view_selector.get_best_view_base(['ad_group_id', 'publisher_id', 'dma'], True), 'mv_pubs_master')  # noqa
        self.assertEqual(view_selector.get_best_view_base(['ad_group_id', 'publisher_id'], False), 'mv_master')
        self.assertEqual(view_selector.get_best_view_base(['ad_group_id', 'publisher_id', 'dma'], False), 'mv_master')  # noqa

        self.assertEqual(view_selector.get_best_view_base(['content_ad_id', 'month']), 'mv_content_ad')
        self.assertEqual(view_selector.get_best_view_base(['content_ad_id', 'source_id']), 'mv_content_ad')
        self.assertEqual(view_selector.get_best_view_base(['content_ad_id', 'source_id', 'age']), 'mv_content_ad_delivery_demo')  # noqa
        self.assertEqual(view_selector.get_best_view_base(['content_ad_id', 'source_id', 'dma']), 'mv_content_ad_delivery_geo')  # noqa
        self.assertEqual(view_selector.get_best_view_base(['content_ad_id', 'publisher_id'], False), 'mv_master')

    def test_get_best_view_conversions(self):
        self.assertEqual(view_selector.get_best_view_conversions(['account_id', 'month']), 'mv_conversions_account')
        self.assertEqual(view_selector.get_best_view_conversions(['account_id', 'source_id']), 'mv_conversions_account')
        self.assertEqual(view_selector.get_best_view_conversions(['account_id', 'source_id', 'age']), None)
        self.assertEqual(view_selector.get_best_view_conversions(['account_id', 'source_id', 'dma']), None)
        self.assertEqual(view_selector.get_best_view_conversions(['account_id', 'campaign_id']), 'mv_conversions_campaign')  # noqa
        self.assertEqual(view_selector.get_best_view_conversions(['account_id', 'ad_group_id']), 'mv_conversions_ad_group')  # noqa

        self.assertEqual(view_selector.get_best_view_conversions(['campaign_id', 'month']), 'mv_conversions_campaign')
        self.assertEqual(view_selector.get_best_view_conversions(['campaign_id', 'source_id']), 'mv_conversions_campaign')  # noqa
        self.assertEqual(view_selector.get_best_view_conversions(['campaign_id', 'source_id', 'age']), None)
        self.assertEqual(view_selector.get_best_view_conversions(['campaign_id', 'source_id', 'dma']), None)
        self.assertEqual(view_selector.get_best_view_conversions(['campaign_id', 'ad_group_id']), 'mv_conversions_ad_group')  # noqa
        self.assertEqual(view_selector.get_best_view_conversions(['campaign_id', 'content_ad_id']), 'mv_conversions_content_ad')  # noqa

        self.assertEqual(view_selector.get_best_view_conversions(['ad_group_id', 'month']), 'mv_conversions_ad_group')
        self.assertEqual(view_selector.get_best_view_conversions(['ad_group_id', 'source_id']), 'mv_conversions_ad_group')  # noqa
        self.assertEqual(view_selector.get_best_view_conversions(['ad_group_id', 'source_id', 'age']), None)
        self.assertEqual(view_selector.get_best_view_conversions(['ad_group_id', 'source_id', 'dma']), None)
        self.assertEqual(view_selector.get_best_view_conversions(['ad_group_id', 'content_ad_id']), 'mv_conversions_content_ad')  # noqa

        self.assertEqual(view_selector.get_best_view_conversions(['ad_group_id', 'publisher_id']), 'mv_conversions')
        self.assertEqual(view_selector.get_best_view_conversions(['ad_group_id', 'publisher_id', 'dma']), None)

        self.assertEqual(view_selector.get_best_view_conversions(['content_ad_id', 'month']), 'mv_conversions_content_ad')  # noqa
        self.assertEqual(view_selector.get_best_view_conversions(['content_ad_id', 'source_id']), 'mv_conversions_content_ad')  # noqa
        self.assertEqual(view_selector.get_best_view_conversions(['content_ad_id', 'source_id', 'age']), None)
        self.assertEqual(view_selector.get_best_view_conversions(['content_ad_id', 'source_id', 'dma']), None)
        self.assertEqual(view_selector.get_best_view_conversions(['content_ad_id', 'publisher_id']), 'mv_conversions')

    def test_get_best_view_touchpoints(self):
        prefix = 'mv_touch'
        self.assertEqual(view_selector.get_best_view_touchpoints(['account_id', 'month']), prefix + '_account')
        self.assertEqual(view_selector.get_best_view_touchpoints(['account_id', 'source_id']), prefix + '_account')
        self.assertEqual(view_selector.get_best_view_touchpoints(['account_id', 'source_id', 'age']), None)
        self.assertEqual(view_selector.get_best_view_touchpoints(['account_id', 'source_id', 'dma']), None)
        self.assertEqual(view_selector.get_best_view_touchpoints(['account_id', 'campaign_id']), prefix + '_campaign')  # noqa
        self.assertEqual(view_selector.get_best_view_touchpoints(['account_id', 'ad_group_id']), prefix + '_ad_group')  # noqa

        self.assertEqual(view_selector.get_best_view_touchpoints(['campaign_id', 'month']), prefix + '_campaign')
        self.assertEqual(view_selector.get_best_view_touchpoints(['campaign_id', 'source_id']), prefix + '_campaign')  # noqa
        self.assertEqual(view_selector.get_best_view_touchpoints(['campaign_id', 'source_id', 'age']), None)
        self.assertEqual(view_selector.get_best_view_touchpoints(['campaign_id', 'source_id', 'dma']), None)
        self.assertEqual(view_selector.get_best_view_touchpoints(['campaign_id', 'ad_group_id']), prefix + '_ad_group')  # noqa
        self.assertEqual(view_selector.get_best_view_touchpoints(['campaign_id', 'content_ad_id']), prefix + '_content_ad')  # noqa

        self.assertEqual(view_selector.get_best_view_touchpoints(['ad_group_id', 'month']), prefix + '_ad_group')
        self.assertEqual(view_selector.get_best_view_touchpoints(['ad_group_id', 'source_id']), prefix + '_ad_group')  # noqa
        self.assertEqual(view_selector.get_best_view_touchpoints(['ad_group_id', 'source_id', 'age']), None)
        self.assertEqual(view_selector.get_best_view_touchpoints(['ad_group_id', 'source_id', 'dma']), None)
        self.assertEqual(view_selector.get_best_view_touchpoints(['ad_group_id', 'content_ad_id']), prefix + '_content_ad')  # noqa

        self.assertEqual(view_selector.get_best_view_touchpoints(['ad_group_id', 'publisher_id']), 'mv_touchpointconversions')  # noqa
        self.assertEqual(view_selector.get_best_view_touchpoints(['ad_group_id', 'publisher_id', 'dma']), None)

        self.assertEqual(view_selector.get_best_view_touchpoints(['content_ad_id', 'month']), prefix + '_content_ad')  # noqa
        self.assertEqual(view_selector.get_best_view_touchpoints(['content_ad_id', 'source_id']), prefix + '_content_ad')  # noqa
        self.assertEqual(view_selector.get_best_view_touchpoints(['content_ad_id', 'source_id', 'age']), None)
        self.assertEqual(view_selector.get_best_view_touchpoints(['content_ad_id', 'source_id', 'dma']), None)
        self.assertEqual(view_selector.get_best_view_touchpoints(['content_ad_id', 'publisher_id']), 'mv_touchpointconversions')  # noqa

    def test_supports_conversions(self):
        self.assertFalse(view_selector.supports_conversions(['dma']))
        self.assertFalse(view_selector.supports_conversions(['device_type']))
        self.assertFalse(view_selector.supports_conversions(['state']))

        self.assertTrue(view_selector.supports_conversions(['content_ad_id']))
        self.assertTrue(view_selector.supports_conversions(['publisher_id']))
        self.assertTrue(view_selector.supports_conversions(['source_id']))
        self.assertTrue(view_selector.supports_conversions(['account_id']))
        self.assertTrue(view_selector.supports_conversions(['week']))
        self.assertTrue(view_selector.supports_conversions(['account_id', 'month']))

        self.assertFalse(view_selector.supports_conversions(['account_id', 'month', 'country']))
