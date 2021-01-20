from decimal import Decimal

import dash.constants


class SourceTypeMixin:
    def get_min_cpc(self, ad_group_settings, bcm_modifiers=None):
        """Some source types have different minimal CPCs depending on the settings.
        Encode these special cases here."""
        min_cpc = self.get_etfm_min_cpc(bcm_modifiers)
        if self.type == dash.constants.SourceType.YAHOO and ad_group_settings.target_devices == [
            dash.constants.AdTargetDevice.DESKTOP
        ]:
            min_cpc = max(min_cpc, Decimal("0.25")) if min_cpc else Decimal("0.25")
        return min_cpc

    def get_min_cpm(self, ad_group_settings, bcm_modifiers=None):
        """Some source types have different minimal CPMs depending on the settings.
        Encode these special cases here."""
        min_cpm = self.get_etfm_min_cpm(bcm_modifiers)
        if self.type == dash.constants.SourceType.YAHOO:
            min_cpm = max(min_cpm, Decimal("0.25")) if min_cpm else Decimal("0.25")
        return min_cpm

    def can_update_state(self):
        return (
            self.available_actions is not None
            and dash.constants.SourceAction.CAN_UPDATE_STATE in self.available_actions
        )

    def can_update_cpc(self):
        return (
            self.available_actions is not None and dash.constants.SourceAction.CAN_UPDATE_CPC in self.available_actions
        )

    def can_update_daily_budget_manual(self):
        return (
            self.available_actions is not None
            and dash.constants.SourceAction.CAN_UPDATE_DAILY_BUDGET_MANUAL in self.available_actions
        )

    def can_update_daily_budget_automatic(self):
        return (
            self.available_actions is not None
            and dash.constants.SourceAction.CAN_UPDATE_DAILY_BUDGET_AUTOMATIC in self.available_actions
        )

    def can_manage_content_ads(self):
        return (
            self.available_actions is not None
            and dash.constants.SourceAction.CAN_MANAGE_CONTENT_ADS in self.available_actions
        )

    def has_3rd_party_dashboard(self):
        return (
            self.available_actions is not None
            and dash.constants.SourceAction.HAS_3RD_PARTY_DASHBOARD in self.available_actions
        )

    def can_modify_start_date(self):
        return (
            self.available_actions is not None
            and dash.constants.SourceAction.CAN_MODIFY_START_DATE in self.available_actions
        )

    def can_modify_end_date(self):
        return (
            self.available_actions is not None
            and dash.constants.SourceAction.CAN_MODIFY_END_DATE in self.available_actions
        )

    def can_modify_device_targeting(self):
        return (
            self.available_actions is not None
            and dash.constants.SourceAction.CAN_MODIFY_DEVICE_TARGETING in self.available_actions
        )

    def can_modify_targeting_for_region_type_automatically(self, region_type):
        if self.available_actions is None:
            return False
        elif region_type == dash.constants.RegionType.COUNTRY:
            return dash.constants.SourceAction.CAN_MODIFY_COUNTRY_TARGETING in self.available_actions
        elif region_type == dash.constants.RegionType.SUBDIVISION:
            return (
                dash.constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_AUTOMATIC in self.available_actions
            )
        elif region_type == dash.constants.RegionType.DMA:
            return (
                dash.constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_AUTOMATIC in self.available_actions
            )

    def can_modify_targeting_for_region_type_manually(self, region_type):
        """Assume automatic targeting support implies manual targeting support

        This addresses the following situation: Imagine targeting
        GB (country) and 693 (DMA) and a SourceType that supports automatic
        DMA targeting and manual country targeting.

        Automatically setting the targeting would be impossible because
        the SourceType does not support modifying country targeting
        automatically.

        Manually setting the targeting would also be impossible because
        the SourceType does not support modifying DMA targeting manually.
        """
        if self.can_modify_targeting_for_region_type_automatically(region_type):
            return True
        if region_type == dash.constants.RegionType.COUNTRY:
            return True
        elif self.available_actions is None:
            return False
        elif region_type == dash.constants.RegionType.SUBDIVISION:
            return dash.constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_MANUAL in self.available_actions
        elif region_type == dash.constants.RegionType.DMA:
            return dash.constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_MANUAL in self.available_actions

    def can_modify_ad_group_name(self):
        return (
            self.available_actions is not None
            and dash.constants.SourceAction.CAN_MODIFY_AD_GROUP_NAME in self.available_actions
        )

    def can_modify_ad_group_iab_category_automatic(self):
        return (
            self.available_actions is not None
            and dash.constants.SourceAction.CAN_MODIFY_AD_GROUP_IAB_CATEGORY_AUTOMATIC in self.available_actions
        )

    def can_modify_ad_group_iab_category_manual(self):
        return (
            self.available_actions is not None
            and dash.constants.SourceAction.CAN_MODIFY_AD_GROUP_IAB_CATEGORY_MANUAL in self.available_actions
        )

    def update_tracking_codes_on_content_ads(self):
        return (
            self.available_actions is not None
            and dash.constants.SourceAction.UPDATE_TRACKING_CODES_ON_CONTENT_ADS in self.available_actions
        )

    def supports_targeting_region_type(self, region_type):
        return self.can_modify_targeting_for_region_type_automatically(
            region_type
        ) or self.can_modify_targeting_for_region_type_manually(region_type)

    def can_fetch_report_by_publisher(self):
        return (
            self.available_actions is not None
            and dash.constants.SourceAction.CAN_FETCH_REPORT_BY_PUBLISHER in self.available_actions
        )

    def can_modify_publisher_blacklist_automatically(self):
        return (
            self.available_actions is not None
            and dash.constants.SourceAction.CAN_MODIFY_PUBLISHER_BLACKLIST_AUTOMATIC in self.available_actions
        )

    def __str__(self):
        return self.type
