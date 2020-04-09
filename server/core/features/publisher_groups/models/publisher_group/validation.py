from django.db.models import Q

import core.models
from utils.exc import ValidationError


class PublisherGroupValidatorMixin(object):
    def clean(self):
        super().clean()
        self._validate_agency_account()
        self._validate_account()
        self._validate_agency()

    def _validate_agency_account(self):
        if self.account is not None and self.agency is not None:
            raise ValidationError(
                errors={
                    "account_id": ["Only one of either account or agency must be set."],
                    "agency_id": ["Only one of either account or agency must be set."],
                }
            )

    def _validate_account(self):
        if self.account is None or self.id is None:
            return

        account_qs = core.models.Account.objects.filter(
            Q(default_whitelist_id=self.id) | Q(default_blacklist_id=self.id)
        )

        if len(account_qs) == 1 and account_qs.get().id != self.account.id:
            raise ValidationError(
                errors={
                    "account_id": "Publisher group is used outside of the scope of {account_name} account. To change the scope of the publisher group to {account_name} stop using it on other accounts (and their campaigns and ad groups) and try again.".format(
                        account_name=self.account
                    )
                }
            )

        account_settings_qs = core.models.settings.AccountSettings.objects.filter(
            Q(whitelist_publisher_groups__contains=[self.id]) | Q(blacklist_publisher_groups__contains=[self.id])
        ).group_current_settings()

        campaign_qs = core.models.Campaign.objects.filter(
            Q(default_whitelist_id=self.id) | Q(default_blacklist_id=self.id)
        )
        campaign_settings_qs = core.models.settings.CampaignSettings.objects.filter(
            Q(whitelist_publisher_groups__contains=[self.id]) | Q(blacklist_publisher_groups__contains=[self.id])
        ).group_current_settings()

        adgroup_qs = core.models.AdGroup.objects.filter(
            Q(default_whitelist_id=self.id) | Q(default_blacklist_id=self.id)
        )
        adgroup_settings_qs = core.models.settings.AdGroupSettings.objects.filter(
            Q(whitelist_publisher_groups__contains=[self.id]) | Q(blacklist_publisher_groups__contains=[self.id])
        ).group_current_settings()

        if (
            account_settings_qs.exclude(account_id=self.account.id).count() > 0
            or campaign_qs.exclude(account_id=self.account.id).count() > 0
            or campaign_settings_qs.exclude(campaign__account_id=self.account.id).count() > 0
            or adgroup_qs.exclude(campaign__account_id=self.account.id).count() > 0
            or adgroup_settings_qs.exclude(ad_group__campaign__account_id=self.account.id).count() > 0
        ):
            raise ValidationError(
                errors={
                    "account_id": "Publisher group is used outside of the scope of {account_name} account. To change the scope of the publisher group to {account_name} stop using it on other accounts (and their campaigns and ad groups) and try again.".format(
                        account_name=self.account
                    )
                }
            )

    def _validate_agency(self):
        if self.agency is None or self.id is None:
            return

        account_qs = core.models.Account.objects.filter(
            Q(default_whitelist_id=self.id) | Q(default_whitelist_id=self.id)
        )
        account_settings_qs = core.models.settings.AccountSettings.objects.filter(
            Q(whitelist_publisher_groups__contains=[self.id]) | Q(blacklist_publisher_groups__contains=[self.id])
        ).group_current_settings()

        campaign_qs = core.models.Campaign.objects.filter(
            Q(default_whitelist_id=self.id) | Q(default_blacklist_id=self.id)
        )
        campaign_settings_qs = core.models.settings.CampaignSettings.objects.filter(
            Q(whitelist_publisher_groups__contains=[self.id]) | Q(blacklist_publisher_groups__contains=[self.id])
        ).group_current_settings()

        adgroup_qs = core.models.AdGroup.objects.filter(
            Q(default_whitelist_id=self.id) | Q(default_blacklist_id=self.id)
        )
        adgroup_settings_qs = core.models.settings.AdGroupSettings.objects.filter(
            Q(whitelist_publisher_groups__contains=[self.id]) | Q(blacklist_publisher_groups__contains=[self.id])
        ).group_current_settings()

        if (
            account_qs.exclude(agency_id=self.agency.id).count() > 0
            or account_settings_qs.exclude(account__agency_id=self.agency.id).count() > 0
            or campaign_qs.exclude(account__agency_id=self.agency.id).count() > 0
            or campaign_settings_qs.exclude(campaign__account__agency_id=self.agency.id).count() > 0
            or adgroup_qs.exclude(campaign__account__agency_id=self.agency.id).count() > 0
            or adgroup_settings_qs.exclude(ad_group__campaign__account__agency_id=self.agency.id).count() > 0
        ):
            raise ValidationError(
                errors={
                    "agency_id": "Publisher group is used outside of the scope of {agency_name} agency. To change the scope of publisher group to {agency_name} stop using it on other agencies (and their accounts, campaigns and ad groups) and try again.".format(
                        agency_name=self.agency
                    )
                }
            )
