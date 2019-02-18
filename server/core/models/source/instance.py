import core.models.default_source_settings
import utils.exc


class SourceMixin:
    def __str__(self):
        deprecated = "(deprecated)" if self.deprecated else ""
        return "{} {}".format(self.name, deprecated)

    def get_clean_slug(self):
        return self.bidder_slug[3:] if self.bidder_slug.startswith("b1_") else self.bidder_slug

    def can_update_state(self):
        return self.source_type.can_update_state() and not self.maintenance and not self.deprecated

    def can_update_cpc(self):
        return self.source_type.can_update_cpc() and not self.maintenance and not self.deprecated

    def can_update_daily_budget_manual(self):
        return self.source_type.can_update_daily_budget_manual() and not self.maintenance and not self.deprecated

    def can_update_daily_budget_automatic(self):
        return self.source_type.can_update_daily_budget_automatic() and not self.maintenance and not self.deprecated

    def can_manage_content_ads(self):
        return self.source_type.can_manage_content_ads() and not self.maintenance and not self.deprecated

    def has_3rd_party_dashboard(self):
        return self.source_type.has_3rd_party_dashboard()

    def can_modify_start_date(self):
        return self.source_type.can_modify_start_date() and not self.maintenance and not self.deprecated

    def can_modify_end_date(self):
        return self.source_type.can_modify_end_date() and not self.maintenance and not self.deprecated

    def can_modify_device_targeting(self):
        return self.source_type.can_modify_device_targeting() and not self.maintenance and not self.deprecated

    def can_modify_targeting_for_region_type_automatically(self, region_type):
        return self.source_type.can_modify_targeting_for_region_type_automatically(region_type)

    def can_modify_targeting_for_region_type_manually(self, region_type):
        return self.source_type.can_modify_targeting_for_region_type_manually(region_type)

    def can_modify_ad_group_name(self):
        return self.source_type.can_modify_ad_group_name() and not self.maintenance and not self.deprecated

    def can_modify_ad_group_iab_category_automatic(self):
        return (
            self.source_type.can_modify_ad_group_iab_category_automatic()
            and not self.maintenance
            and not self.deprecated
        )

    def can_modify_ad_group_iab_category_manual(self):
        return (
            self.source_type.can_modify_ad_group_iab_category_manual() and not self.maintenance and not self.deprecated
        )

    def update_tracking_codes_on_content_ads(self):
        return self.source_type.update_tracking_codes_on_content_ads()

    def can_fetch_report_by_publisher(self):
        return self.source_type.can_fetch_report_by_publisher()

    def can_modify_publisher_blacklist_automatically(self):
        return (
            self.source_type.can_modify_publisher_blacklist_automatically()
            and not self.maintenance
            and not self.deprecated
        )

    def can_modify_retargeting_automatically(self):
        return self.supports_retargeting and not self.maintenance and not self.deprecated

    def can_modify_retargeting_manually(self):
        return self.supports_retargeting_manually and not self.maintenance and not self.deprecated

    def get_default_settings(self):
        try:
            default_settings = self.defaultsourcesettings
        except core.models.default_source_settings.DefaultSourceSettings.DoesNotExist:
            raise utils.exc.MissingDataError("No default settings set for {}.".format(self.name))

        if not default_settings.credentials:
            raise utils.exc.MissingDataError("No default credentials set in {}.".format(default_settings))
        return default_settings
