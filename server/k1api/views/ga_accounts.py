import datetime
import logging

from django.core.cache import caches

import dash.constants
import dash.features.ga
import dash.models
from utils import cache_helper
from utils import db_router

from .base import K1APIView

logger = logging.getLogger(__name__)


class GAAccountsView(K1APIView):
    @db_router.use_read_replica()
    def get(self, request):
        date_since = request.GET.get("date_since")

        cache = caches["dash_db_cache"]
        cache_key = cache_helper.get_cache_key("ga-accounts", date_since)
        response = cache.get(cache_key, None)
        if response is not None:
            return self.response_ok(response)

        all_active_campaign_ids = set(
            dash.models.Campaign.objects.all().exclude_archived().values_list("id", flat=True)
        )
        if "campaigns" in request.GET:
            all_active_campaign_ids = set(request.GET.get("campaigns", "").split(","))
        all_current_settings = dash.models.CampaignSettings.objects.filter(
            campaign_id__in=all_active_campaign_ids
        ).group_current_settings()
        ga_accounts = set()
        for current_settings in all_current_settings:
            self._extract_ga_settings(ga_accounts, current_settings)
        if date_since:
            valid_previous_settings = (
                dash.models.CampaignSettings.objects.filter(
                    campaign_id__in=all_active_campaign_ids,
                    created_dt__lte=datetime.datetime.strptime(date_since, "%Y-%m-%d").date(),
                )
                .order_by("campaign_id", "-created_dt")
                .distinct("campaign")
            )
            for previous_settings in valid_previous_settings:
                self._extract_ga_settings(ga_accounts, previous_settings)
            all_intermediate_settings = (
                dash.models.CampaignSettings.objects.filter(
                    campaign_id__in=all_active_campaign_ids,
                    created_dt__gte=datetime.datetime.strptime(date_since, "%Y-%m-%d").date(),
                )
                .exclude(pk__in=set(s.pk for s in all_current_settings) | set(s.pk for s in valid_previous_settings))
                .exclude(ga_property_id__in=set(ga_property_id for _, _, ga_property_id in ga_accounts))
            )
            for previous_settings in all_intermediate_settings:
                self._extract_ga_settings(ga_accounts, previous_settings)
        ga_accounts_dicts = [
            {"account_id": account_id, "ga_account_id": ga_account_id, "ga_web_property_id": ga_web_property_id}
            for account_id, ga_account_id, ga_web_property_id in sorted(ga_accounts)
        ]
        ga_account_ids = set(ga_account_id for _, ga_account_id, _ in ga_accounts)

        response = {
            "ga_accounts": list(ga_accounts_dicts),
            "service_email_mapping": self._get_service_email_mapping(ga_account_ids),
        }
        cache.set(cache_key, response, timeout=60 * 60)
        return self.response_ok(response)

    def _extract_ga_settings(self, ga_accounts, campaign_settings):
        if not (
            campaign_settings.enable_ga_tracking
            and campaign_settings.ga_tracking_type == dash.constants.GATrackingType.API
            and campaign_settings.ga_property_id
        ):
            return
        ga_property_id = campaign_settings.ga_property_id
        ga_accounts.add(
            (
                campaign_settings.campaign.account_id,
                dash.features.ga.extract_ga_account_id(ga_property_id),
                ga_property_id,
            )
        )

    def _get_service_email_mapping(self, ga_account_ids):
        mapping = {
            m.customer_ga_account_id: m.zem_ga_account_email
            for m in dash.features.ga.GALinkedAccounts.objects.filter(customer_ga_account_id__in=ga_account_ids)
        }
        # TODO: sigi 8.2.2018
        # both zem users have access to the same profile but only one is reciving data
        if "5428971" in mapping:
            mapping["5428971"] = "account-1@zemanta-api.iam.gserviceaccount.com"
        return mapping
