from django.test import TestCase

from redshiftapi import view_selector


class ViewSelectorTest(TestCase):
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
        self.assertEqual(
            view_selector.get_best_view_base(["campaign_id", "source_id", "dma"], False), "mv_campaign_geo"
        )  # noqa
        self.assertEqual(view_selector.get_best_view_base(["campaign_id", "ad_group_id"], False), "mv_adgroup")
        self.assertEqual(view_selector.get_best_view_base(["campaign_id", "content_ad_id"], False), "mv_contentad")

        self.assertEqual(view_selector.get_best_view_base(["ad_group_id", "month"], False), "mv_adgroup")
        self.assertEqual(view_selector.get_best_view_base(["ad_group_id", "source_id"], False), "mv_adgroup")
        self.assertEqual(view_selector.get_best_view_base(["ad_group_id", "source_id", "age"], False), "mv_master")
        self.assertEqual(view_selector.get_best_view_base(["ad_group_id", "source_id", "dma"], False), "mv_adgroup_geo")
        self.assertEqual(view_selector.get_best_view_base(["ad_group_id", "content_ad_id"], False), "mv_contentad")

        self.assertEqual(view_selector.get_best_view_base(["ad_group_id", "publisher_id"], True), "mv_adgroup_pubs")
        self.assertEqual(
            view_selector.get_best_view_base(["ad_group_id", "publisher_id", "dma"], True), "mv_master_pubs"
        )  # noqa
        self.assertEqual(view_selector.get_best_view_base(["ad_group_id", "publisher_id"], False), "mv_master")
        self.assertEqual(
            view_selector.get_best_view_base(["ad_group_id", "publisher_id", "dma"], False), "mv_master"
        )  # noqa

        self.assertEqual(view_selector.get_best_view_base(["content_ad_id", "month"], False), "mv_contentad")
        self.assertEqual(view_selector.get_best_view_base(["content_ad_id", "source_id"], False), "mv_contentad")
        self.assertEqual(
            view_selector.get_best_view_base(["content_ad_id", "source_id", "age"], False), "mv_master"
        )  # noqa
        self.assertEqual(
            view_selector.get_best_view_base(["content_ad_id", "source_id", "dma"], False), "mv_contentad_geo"
        )  # noqa
        self.assertEqual(view_selector.get_best_view_base(["content_ad_id", "publisher_id"], False), "mv_master")

    def test_get_best_view_conversions(self):
        self.assertEqual(view_selector.get_best_view_conversions(["account_id", "month"]), "mv_account_conv")  # noqa
        self.assertEqual(
            view_selector.get_best_view_conversions(["account_id", "source_id"]), "mv_account_conv"
        )  # noqa
        self.assertEqual(view_selector.get_best_view_conversions(["account_id", "source_id", "age"]), None)
        self.assertEqual(view_selector.get_best_view_conversions(["account_id", "source_id", "dma"]), None)
        self.assertEqual(
            view_selector.get_best_view_conversions(["account_id", "campaign_id"]), "mv_campaign_conv"
        )  # noqa
        self.assertEqual(
            view_selector.get_best_view_conversions(["account_id", "ad_group_id"]), "mv_adgroup_conv"
        )  # noqa

        self.assertEqual(view_selector.get_best_view_conversions(["campaign_id", "month"]), "mv_campaign_conv")
        self.assertEqual(
            view_selector.get_best_view_conversions(["campaign_id", "source_id"]), "mv_campaign_conv"
        )  # noqa
        self.assertEqual(view_selector.get_best_view_conversions(["campaign_id", "source_id", "age"]), None)
        self.assertEqual(view_selector.get_best_view_conversions(["campaign_id", "source_id", "dma"]), None)
        self.assertEqual(
            view_selector.get_best_view_conversions(["campaign_id", "ad_group_id"]), "mv_adgroup_conv"
        )  # noqa
        self.assertEqual(
            view_selector.get_best_view_conversions(["campaign_id", "content_ad_id"]), "mv_contentad_conv"
        )  # noqa

        self.assertEqual(view_selector.get_best_view_conversions(["ad_group_id", "month"]), "mv_adgroup_conv")  # noqa
        self.assertEqual(
            view_selector.get_best_view_conversions(["ad_group_id", "source_id"]), "mv_adgroup_conv"
        )  # noqa
        self.assertEqual(view_selector.get_best_view_conversions(["ad_group_id", "source_id", "age"]), None)
        self.assertEqual(view_selector.get_best_view_conversions(["ad_group_id", "source_id", "dma"]), None)
        self.assertEqual(
            view_selector.get_best_view_conversions(["ad_group_id", "content_ad_id"]), "mv_contentad_conv"
        )  # noqa

        self.assertEqual(
            view_selector.get_best_view_conversions(["ad_group_id", "publisher_id"]), "mv_conversions"
        )  # noqa
        self.assertEqual(view_selector.get_best_view_conversions(["ad_group_id", "publisher_id", "dma"]), None)
        self.assertEqual(
            view_selector.get_best_view_conversions(["ad_group_id", "content_ad_id", "publisher_id"]), "mv_conversions"
        )  # noqa

        self.assertEqual(
            view_selector.get_best_view_conversions(["content_ad_id", "month"]), "mv_contentad_conv"
        )  # noqa
        self.assertEqual(
            view_selector.get_best_view_conversions(["content_ad_id", "source_id"]), "mv_contentad_conv"
        )  # noqa
        self.assertEqual(view_selector.get_best_view_conversions(["content_ad_id", "source_id", "age"]), None)
        self.assertEqual(view_selector.get_best_view_conversions(["content_ad_id", "source_id", "dma"]), None)
        self.assertEqual(
            view_selector.get_best_view_conversions(["content_ad_id", "publisher_id"]), "mv_conversions"
        )  # noqa

    def test_get_best_view_touchpoints(self):
        self.assertEqual(view_selector.get_best_view_touchpoints(["account_id", "month"]), "mv_account_touch")
        self.assertEqual(
            view_selector.get_best_view_touchpoints(["account_id", "source_id"]), "mv_account_touch"
        )  # noqa
        self.assertEqual(view_selector.get_best_view_touchpoints(["account_id", "source_id", "age"]), None)
        self.assertEqual(
            view_selector.get_best_view_touchpoints(["account_id", "source_id", "dma"]), "mv_account_touch_geo"
        )  # noqa
        self.assertEqual(
            view_selector.get_best_view_touchpoints(["account_id", "source_id", "device_type"]),
            "mv_account_touch_device",
        )  # noqa
        self.assertEqual(
            view_selector.get_best_view_touchpoints(["account_id", "campaign_id"]), "mv_campaign_touch"
        )  # noqa
        self.assertEqual(
            view_selector.get_best_view_touchpoints(["account_id", "ad_group_id"]), "mv_adgroup_touch"
        )  # noqa

        self.assertEqual(view_selector.get_best_view_touchpoints(["campaign_id", "month"]), "mv_campaign_touch")
        self.assertEqual(
            view_selector.get_best_view_touchpoints(["campaign_id", "source_id"]), "mv_campaign_touch"
        )  # noqa
        self.assertEqual(view_selector.get_best_view_touchpoints(["campaign_id", "source_id", "age"]), None)
        self.assertEqual(
            view_selector.get_best_view_touchpoints(["campaign_id", "source_id", "dma"]), "mv_campaign_touch_geo"
        )  # noqa
        self.assertEqual(
            view_selector.get_best_view_touchpoints(["campaign_id", "ad_group_id"]), "mv_adgroup_touch"
        )  # noqa
        self.assertEqual(
            view_selector.get_best_view_touchpoints(["campaign_id", "content_ad_id"]), "mv_contentad_touch"
        )  # noqa

        self.assertEqual(view_selector.get_best_view_touchpoints(["ad_group_id", "month"]), "mv_adgroup_touch")
        self.assertEqual(
            view_selector.get_best_view_touchpoints(["ad_group_id", "source_id"]), "mv_adgroup_touch"
        )  # noqa
        self.assertEqual(view_selector.get_best_view_touchpoints(["ad_group_id", "source_id", "age"]), None)
        self.assertEqual(
            view_selector.get_best_view_touchpoints(["ad_group_id", "source_id", "dma"]), "mv_adgroup_touch_geo"
        )  # noqa
        self.assertEqual(
            view_selector.get_best_view_touchpoints(["ad_group_id", "content_ad_id"]), "mv_contentad_touch"
        )  # noqa
        self.assertEqual(
            view_selector.get_best_view_touchpoints(["ad_group_id", "content_ad_id", "publisher_id"]),
            "mv_touchpointconversions",
        )  # noqa
        self.assertEqual(
            view_selector.get_best_view_touchpoints(["ad_group_id", "content_ad_id", "publisher_id", "placement_id"]),
            "mv_touchpointconversions",
        )  # noqa

        self.assertEqual(
            view_selector.get_best_view_touchpoints(["ad_group_id", "publisher_id"]), "mv_touchpointconversions"
        )  # noqa
        self.assertEqual(
            view_selector.get_best_view_touchpoints(["ad_group_id", "placement_id"]), "mv_adgroup_touch_placement"
        )  # noqa
        self.assertEqual(
            view_selector.get_best_view_touchpoints(["ad_group_id", "publisher_id", "placement_id"]),
            "mv_touchpointconversions",
        )  # noqa
        self.assertEqual(
            view_selector.get_best_view_touchpoints(["ad_group_id", "publisher_id", "dma"]), "mv_touchpointconversions"
        )  # noqa

        self.assertEqual(
            view_selector.get_best_view_touchpoints(["content_ad_id", "month"]), "mv_contentad_touch"
        )  # noqa
        self.assertEqual(
            view_selector.get_best_view_touchpoints(["content_ad_id", "source_id"]), "mv_contentad_touch"
        )  # noqa
        self.assertEqual(view_selector.get_best_view_touchpoints(["content_ad_id", "source_id", "age"]), None)
        self.assertEqual(
            view_selector.get_best_view_touchpoints(["content_ad_id", "source_id", "dma"]), "mv_contentad_touch_geo"
        )  # noqa
        self.assertEqual(
            view_selector.get_best_view_touchpoints(["content_ad_id", "publisher_id"]), "mv_touchpointconversions"
        )  # noqa
        self.assertEqual(
            view_selector.get_best_view_touchpoints(["content_ad_id", "placement_id"]), "mv_touchpointconversions"
        )  # noqa

    def test_supports_conversions(self):
        self.assertFalse(view_selector.supports_conversions("mv_master", None))
        self.assertTrue(view_selector.supports_conversions("mv_adgroup", "mv_adgroup_conv"))
