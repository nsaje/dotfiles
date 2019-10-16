import datetime
from collections import defaultdict

from django.core.cache import caches

import dash.constants
import dash.features.ga
import dash.models
import structlog
from utils import cache_helper
from utils import db_router

from .base import K1APIView

logger = structlog.get_logger(__name__)


OEN_ACCOUNT_ID = 305


class GAAccountsView(K1APIView):
    @db_router.use_read_replica()
    def get(self, request):
        date_since = request.GET.get("date_since")
        limit = int(request.GET.get("limit", 100))
        marker = request.GET.get("marker")

        cache = caches["dash_db_cache"]
        cache_key = cache_helper.get_cache_key("ga-accounts", date_since, limit, marker)
        response = cache.get(cache_key, None)
        if response is not None:
            return self.response_ok(response)

        accounts = dash.models.Account.objects.all().exclude_archived().exclude(id__in=[OEN_ACCOUNT_ID]).order_by("id")
        if marker:
            accounts = accounts.filter(pk__gt=int(marker))
        accounts = accounts[:limit]
        campaigns = dash.models.Campaign.objects.filter(account__in=accounts).exclude_archived()

        active_campaign_ids = set(campaigns.values_list("id", flat=True))
        if "campaigns" in request.GET:
            active_campaign_ids = set(request.GET.get("campaigns", "").split(","))
        all_current_settings = (
            dash.models.CampaignSettings.objects.filter(campaign_id__in=active_campaign_ids)
            .group_current_settings()
            .select_related("campaign")
        )
        ga_accounts = set()
        for current_settings in all_current_settings:
            self._extract_ga_settings(ga_accounts, current_settings)
        if date_since:
            valid_previous_settings = (
                dash.models.CampaignSettings.objects.filter(
                    campaign_id__in=active_campaign_ids,
                    created_dt__lte=datetime.datetime.strptime(date_since, "%Y-%m-%d").date(),
                )
                .order_by("campaign_id", "-created_dt")
                .select_related("campaign")
                .distinct("campaign")
            )
            for previous_settings in valid_previous_settings:
                self._extract_ga_settings(ga_accounts, previous_settings)
            all_intermediate_settings = (
                dash.models.CampaignSettings.objects.filter(
                    campaign_id__in=active_campaign_ids,
                    created_dt__gte=datetime.datetime.strptime(date_since, "%Y-%m-%d").date(),
                )
                .exclude(pk__in=set(s.pk for s in all_current_settings) | set(s.pk for s in valid_previous_settings))
                .exclude(ga_property_id__in=set(ga_property_id for _, _, ga_property_id in ga_accounts))
                .select_related("campaign")
            )
            for previous_settings in all_intermediate_settings:
                self._extract_ga_settings(ga_accounts, previous_settings)

        response = self._construct_response(accounts, ga_accounts)
        cache.set(cache_key, response, timeout=60 * 60)
        return self.response_ok(response)

    def _construct_response(self, accounts, ga_accounts):
        ga_account_ids = set(ga_account_id for _, ga_account_id, _ in ga_accounts)
        service_email_mapping = self._get_service_email_mapping(ga_account_ids)

        ga_accounts_map = defaultdict(list)
        for account_id, ga_account_id, ga_web_property_id in ga_accounts:
            ga_accounts_map[account_id].append((account_id, ga_account_id, ga_web_property_id))

        ga_accounts_dicts = []
        for account in accounts:
            if account.id not in ga_accounts_map:
                ga_accounts_dicts.append(
                    {"account_id": account.id, "ga_account_id": None, "ga_web_property_id": None, "service_email": None}
                )
                continue
            for account_id, ga_account_id, ga_web_property_id in sorted(ga_accounts_map[account.id]):
                ga_accounts_dicts.append(
                    {
                        "account_id": account_id,
                        "ga_account_id": ga_account_id,
                        "ga_web_property_id": ga_web_property_id,
                        "service_email": service_email_mapping.get(ga_account_id),
                    }
                )
        return ga_accounts_dicts

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
