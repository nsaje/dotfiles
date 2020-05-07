from django.test import TestCase

from redshiftapi import view_selector


class ViewSelectorTest(TestCase):
    # fmt: off
    def test_get_best_view_base(self):
        self.assertEqual(view_selector.get_best_view_base(["account_id", "month"], False), "mv_account")
        self.assertEqual(view_selector.get_best_view_base(["account_id", "source_id"], False), "mv_account")
        self.assertEqual(view_selector.get_best_view_base(["account_id", "source_id", "age"], False), "mv_master")
        self.assertEqual(view_selector.get_best_view_base(["account_id", "source_id", "dma"], False), "mv_account_geo")
        self.assertEqual(view_selector.get_best_view_base(["account_id", "campaign_id"], False), "mv_campaign")
        self.assertEqual(view_selector.get_best_view_base(["account_id", "ad_group_id"], False), "mv_adgroup")

        self.assertEqual(view_selector.get_best_view_base(["campaign_id", "month"], False), "mv_campaign")
        self.assertEqual(view_selector.get_best_view_base(["campaign_id", "source_id"], False), "mv_campaign")
        self.assertEqual(view_selector.get_best_view_base(["campaign_id", "source_id", "age"], False), "mv_master")
        self.assertEqual(view_selector.get_best_view_base(["campaign_id", "source_id", "dma"], False), "mv_campaign_geo")
        self.assertEqual(view_selector.get_best_view_base(["campaign_id", "ad_group_id"], False), "mv_adgroup")
        self.assertEqual(view_selector.get_best_view_base(["campaign_id", "content_ad_id"], False), "mv_contentad")

        self.assertEqual(view_selector.get_best_view_base(["ad_group_id", "month"], False), "mv_adgroup")
        self.assertEqual(view_selector.get_best_view_base(["ad_group_id", "source_id"], False), "mv_adgroup")
        self.assertEqual(view_selector.get_best_view_base(["ad_group_id", "source_id", "age"], False), "mv_master")
        self.assertEqual(view_selector.get_best_view_base(["ad_group_id", "source_id", "dma"], False), "mv_adgroup_geo")
        self.assertEqual(view_selector.get_best_view_base(["ad_group_id", "content_ad_id"], False), "mv_contentad")

        self.assertEqual(view_selector.get_best_view_base(["ad_group_id", "publisher_id"], True), "mv_adgroup_pubs")
        self.assertEqual(view_selector.get_best_view_base(["ad_group_id", "publisher_id", "dma"], True), "mv_master_pubs")
        self.assertEqual(view_selector.get_best_view_base(["ad_group_id", "publisher_id"], False), "mv_master")
        self.assertEqual(view_selector.get_best_view_base(["ad_group_id", "publisher_id", "dma"], False), "mv_master")

        self.assertEqual(view_selector.get_best_view_base(["content_ad_id", "month"], False), "mv_contentad")
        self.assertEqual(view_selector.get_best_view_base(["content_ad_id", "source_id"], False), "mv_contentad")
        self.assertEqual(view_selector.get_best_view_base(["content_ad_id", "source_id", "age"], False), "mv_master")
        self.assertEqual(view_selector.get_best_view_base(["content_ad_id", "source_id", "dma"], False), "mv_contentad_geo")
        self.assertEqual(view_selector.get_best_view_base(["content_ad_id", "publisher_id"], False), "mv_master")

        self.assertEqual(view_selector.get_best_view_base(["account_id", "placement_id", "placement_type"], True), "mv_account_placement")
        self.assertEqual(view_selector.get_best_view_base(["account_id", "publisher_id", "placement_id", "placement_type"], True), "mv_account_placement")
        self.assertEqual(view_selector.get_best_view_base(["campaign_id", "placement_id", "placement_type"], True), "mv_campaign_placement")
        self.assertEqual(view_selector.get_best_view_base(["account_id", "campaign_id", "publisher_id", "placement_id", "placement_type"], True), "mv_campaign_placement")
        self.assertEqual(view_selector.get_best_view_base(["ad_group_id", "placement_id", "placement_type"], True), "mv_adgroup_placement")
        self.assertEqual(view_selector.get_best_view_base(["account_id", "campaign_id", "ad_group_id", "publisher_id", "placement_id", "placement_type"], True), "mv_adgroup_placement")

    def test_get_best_view_conversions(self):
        self.assertEqual(view_selector.get_best_view_conversions(["account_id", "month"]), "mv_account_conv")
        self.assertEqual(view_selector.get_best_view_conversions(["account_id", "source_id"]), "mv_account_conv")
        self.assertEqual(view_selector.get_best_view_conversions(["account_id", "source_id", "age"]), None)
        self.assertEqual(view_selector.get_best_view_conversions(["account_id", "source_id", "dma"]), None)
        self.assertEqual(view_selector.get_best_view_conversions(["account_id", "campaign_id"]), "mv_campaign_conv")
        self.assertEqual(view_selector.get_best_view_conversions(["account_id", "ad_group_id"]), "mv_adgroup_conv")

        self.assertEqual(view_selector.get_best_view_conversions(["campaign_id", "month"]), "mv_campaign_conv")
        self.assertEqual(view_selector.get_best_view_conversions(["campaign_id", "source_id"]), "mv_campaign_conv")
        self.assertEqual(view_selector.get_best_view_conversions(["campaign_id", "source_id", "age"]), None)
        self.assertEqual(view_selector.get_best_view_conversions(["campaign_id", "source_id", "dma"]), None)
        self.assertEqual(view_selector.get_best_view_conversions(["campaign_id", "ad_group_id"]), "mv_adgroup_conv")
        self.assertEqual(view_selector.get_best_view_conversions(["campaign_id", "content_ad_id"]), "mv_contentad_conv")

        self.assertEqual(view_selector.get_best_view_conversions(["ad_group_id", "month"]), "mv_adgroup_conv")
        self.assertEqual(view_selector.get_best_view_conversions(["ad_group_id", "source_id"]), "mv_adgroup_conv")
        self.assertEqual(view_selector.get_best_view_conversions(["ad_group_id", "source_id", "age"]), None)
        self.assertEqual(view_selector.get_best_view_conversions(["ad_group_id", "source_id", "dma"]), None)
        self.assertEqual(view_selector.get_best_view_conversions(["ad_group_id", "content_ad_id"]), "mv_contentad_conv")

        self.assertEqual(view_selector.get_best_view_conversions(["ad_group_id", "publisher_id"]), "mv_conversions")
        self.assertEqual(view_selector.get_best_view_conversions(["ad_group_id", "publisher_id", "dma"]), None)
        self.assertEqual(view_selector.get_best_view_conversions(["ad_group_id", "content_ad_id", "publisher_id"]), "mv_conversions")

        self.assertEqual(view_selector.get_best_view_conversions(["content_ad_id", "month"]), "mv_contentad_conv")
        self.assertEqual(view_selector.get_best_view_conversions(["content_ad_id", "source_id"]), "mv_contentad_conv")
        self.assertEqual(view_selector.get_best_view_conversions(["content_ad_id", "source_id", "age"]), None)
        self.assertEqual(view_selector.get_best_view_conversions(["content_ad_id", "source_id", "dma"]), None)
        self.assertEqual(view_selector.get_best_view_conversions(["content_ad_id", "publisher_id"]), "mv_conversions")

    def test_get_best_view_touchpoints(self):
        self.assertEqual(view_selector.get_best_view_touchpoints(["account_id", "month"]), "mv_account_touch")
        self.assertEqual(view_selector.get_best_view_touchpoints(["account_id", "source_id"]), "mv_account_touch")
        self.assertEqual(view_selector.get_best_view_touchpoints(["account_id", "source_id", "age"]), None)
        self.assertEqual(view_selector.get_best_view_touchpoints(["account_id", "source_id", "dma"]), "mv_account_touch_geo")
        self.assertEqual(view_selector.get_best_view_touchpoints(["account_id", "source_id", "device_type"]), "mv_account_touch_device",)
        self.assertEqual(view_selector.get_best_view_touchpoints(["account_id", "campaign_id"]), "mv_campaign_touch")
        self.assertEqual(view_selector.get_best_view_touchpoints(["account_id", "ad_group_id"]), "mv_adgroup_touch")

        self.assertEqual(view_selector.get_best_view_touchpoints(["campaign_id", "month"]), "mv_campaign_touch")
        self.assertEqual(view_selector.get_best_view_touchpoints(["campaign_id", "source_id"]), "mv_campaign_touch")
        self.assertEqual(view_selector.get_best_view_touchpoints(["campaign_id", "source_id", "age"]), None)
        self.assertEqual(view_selector.get_best_view_touchpoints(["campaign_id", "source_id", "dma"]), "mv_campaign_touch_geo")
        self.assertEqual(view_selector.get_best_view_touchpoints(["campaign_id", "ad_group_id"]), "mv_adgroup_touch")
        self.assertEqual(view_selector.get_best_view_touchpoints(["campaign_id", "content_ad_id"]), "mv_contentad_touch")

        self.assertEqual(view_selector.get_best_view_touchpoints(["ad_group_id", "month"]), "mv_adgroup_touch")
        self.assertEqual(view_selector.get_best_view_touchpoints(["ad_group_id", "source_id"]), "mv_adgroup_touch")
        self.assertEqual(view_selector.get_best_view_touchpoints(["ad_group_id", "source_id", "age"]), None)
        self.assertEqual(view_selector.get_best_view_touchpoints(["ad_group_id", "source_id", "dma"]), "mv_adgroup_touch_geo")
        self.assertEqual(view_selector.get_best_view_touchpoints(["ad_group_id", "content_ad_id"]), "mv_contentad_touch")
        self.assertEqual(
            view_selector.get_best_view_touchpoints(["account_id", "campaign_id", "ad_group_id", "content_ad_id", "publisher_id"]),
            "mv_touchpointconversions",
        )
        self.assertEqual(
            view_selector.get_best_view_touchpoints(["account_id", "campaign_id", "ad_group_id", "content_ad_id", "publisher_id", "placement_id"]),
            "mv_touchpointconversions",
        )
        self.assertEqual(
            view_selector.get_best_view_touchpoints(["account_id", "campaign_id", "ad_group_id", "content_ad_id", "publisher_id", "placement_id", "placement_type"]),
            "mv_touchpointconversions",
        )

        self.assertEqual(view_selector.get_best_view_touchpoints(["account_id", "publisher_id"]), "mv_touchpointconversions")
        self.assertEqual(view_selector.get_best_view_touchpoints(["campaign_id", "publisher_id"]), "mv_touchpointconversions")
        self.assertEqual(view_selector.get_best_view_touchpoints(["ad_group_id", "publisher_id"]), "mv_touchpointconversions")

        self.assertEqual(view_selector.get_best_view_touchpoints(["account_id", "placement_id", "placement_type"]), "mv_account_touch_placement")
        self.assertEqual(view_selector.get_best_view_touchpoints(["account_id", "publisher_id", "placement_id", "placement_type"]), "mv_touchpointconversions")
        self.assertEqual(view_selector.get_best_view_touchpoints(["account_id", "publisher_id", "dma"]), "mv_touchpointconversions")

        self.assertEqual(view_selector.get_best_view_touchpoints(["campaign_id", "placement_id", "placement_type"]), "mv_campaign_touch_placement")
        self.assertEqual(view_selector.get_best_view_touchpoints(["campaign_id", "publisher_id", "placement_id", "placement_type"]), "mv_touchpointconversions")
        self.assertEqual(view_selector.get_best_view_touchpoints(["campaign_id", "publisher_id", "dma"]), "mv_touchpointconversions")

        self.assertEqual(view_selector.get_best_view_touchpoints(["ad_group_id", "placement_id", "placement_type"]), "mv_adgroup_touch_placement")
        self.assertEqual(view_selector.get_best_view_touchpoints(["ad_group_id", "publisher_id", "placement_id", "placement_type"]), "mv_touchpointconversions")
        self.assertEqual(view_selector.get_best_view_touchpoints(["ad_group_id", "publisher_id", "dma"]), "mv_touchpointconversions")

        self.assertEqual(view_selector.get_best_view_touchpoints(["content_ad_id", "month"]), "mv_contentad_touch")
        self.assertEqual(view_selector.get_best_view_touchpoints(["content_ad_id", "source_id"]), "mv_contentad_touch")
        self.assertEqual(view_selector.get_best_view_touchpoints(["content_ad_id", "source_id", "age"]), None)
        self.assertEqual(view_selector.get_best_view_touchpoints(["content_ad_id", "source_id", "dma"]), "mv_contentad_touch_geo")
        self.assertEqual(view_selector.get_best_view_touchpoints(["content_ad_id", "publisher_id"]), "mv_touchpointconversions")
        self.assertEqual(view_selector.get_best_view_touchpoints(["content_ad_id", "placement_id"]), "mv_touchpointconversions")
        self.assertEqual(view_selector.get_best_view_touchpoints(["content_ad_id", "placement_type"]), "mv_touchpointconversions")

    def test_supports_conversions(self):
        self.assertFalse(view_selector.supports_conversions("mv_master", None))
        self.assertTrue(view_selector.supports_conversions("mv_adgroup", "mv_adgroup_conv"))
    # fmt: on
