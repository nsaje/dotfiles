import logging

from django.conf import settings

import dash.constants
import dash.models
from core.publisher_groups import publisher_group_helpers
from utils import db_for_reads
import automation.campaignstop.service
import dash.features.custom_flags

from .base import K1APIView

logger = logging.getLogger(__name__)


EVENT_RETARGET_ADGROUP = "redirect_adgroup"
EVENT_CUSTOM_AUDIENCE = "aud"

BLOCKED_AGENCIES = (151, 165, 191)
BLOCKED_ACCOUNTS = (523, )


class AdGroupsView(K1APIView):
    """
    Returns a list of non-archived ad groups together with their current settings.

    Filterable by ad_group_ids, source_type and slug.
    """

    @db_for_reads.use_read_replica()
    def get(self, request):
        limit = int(request.GET.get('limit', 1000000))
        marker = request.GET.get('marker')
        ad_group_ids = request.GET.get('ad_group_ids')
        source_types = request.GET.get('source_types')
        slugs = request.GET.get('source_slugs')
        if ad_group_ids:
            ad_group_ids = ad_group_ids.split(',')
        if source_types:
            source_types = source_types.split(',')
        if slugs:
            slugs = slugs.split(',')

        ad_groups,\
            campaigns_budgets_map,\
            campaignstop_states = self._get_ad_groups(ad_group_ids, source_types, slugs, marker, limit)

        campaign_ids = set(ad_group.campaign_id for ad_group in ad_groups)
        campaign_goal_types = self._get_campaign_goal_types(list(campaign_ids))
        campaign_goals = self._get_campaign_goals(list(campaign_ids))

        all_custom_flags = {
            flag: False
            for flag in dash.features.custom_flags.CustomFlag.objects.all().values_list(
                'id', flat=True
            )
        }

        ad_group_dicts = []
        for ad_group in ad_groups:
            if ad_group.settings is None:
                logger.error('K1API - ad group settings are None')
                continue

            agency_settings = None
            agency_name = ''
            if ad_group.campaign.account.agency:
                agency_settings = ad_group.campaign.account.agency.settings
                agency_name = ad_group.campaign.account.agency.name

            blacklist = ad_group.settings.blacklist_publisher_groups
            whitelist = ad_group.settings.whitelist_publisher_groups

            ad_group = ad_group.settings.ad_group
            blacklist, whitelist = publisher_group_helpers.concat_publisher_group_targeting(
                ad_group, ad_group.settings,
                ad_group.campaign, ad_group.campaign.settings,
                ad_group.campaign.account, ad_group.campaign.account.settings,
                ad_group.campaign.account.agency, agency_settings,
                include_global=False  # global blacklist is handled separately by the bidder, no need to duplicate work
            )

            license_fee = None
            margin = None
            if ad_group.campaign_id in campaigns_budgets_map:
                license_fee = campaigns_budgets_map[ad_group.campaign_id].credit.license_fee
                margin = campaigns_budgets_map[ad_group.campaign_id].margin

            max_cpm = ad_group.settings.get_external_max_cpm(
                ad_group.campaign.account,
                license_fee,
                margin
            )
            b1_sources_group_daily_budget = ad_group.settings.get_external_b1_sources_group_daily_budget(
                ad_group.campaign.account,
                license_fee,
                margin
            )
            b1_sources_group_cpc_cc = ad_group.settings.get_external_b1_sources_group_cpc_cc(
                ad_group.campaign.account,
                license_fee,
                margin,
            )

            # FIXME: k1 doesn't update missing keys, find a better solution
            flags = {}
            flags.update(all_custom_flags)
            flags.update(ad_group.get_all_custom_flags())

            ad_group_dict = {
                'id': ad_group.id,
                'name': ad_group.name,
                'external_name': ad_group.get_external_name(),
                'start_date': ad_group.settings.start_date,
                'end_date': self._get_end_date(ad_group.settings, campaignstop_states),
                'time_zone': settings.DEFAULT_TIME_ZONE,
                'brand_name': ad_group.settings.brand_name,
                'display_url': ad_group.settings.display_url,
                'tracking_codes': ad_group.settings.get_tracking_codes(),
                'target_devices': ad_group.settings.target_devices,
                'target_os': ad_group.settings.target_os,
                'target_browsers': ad_group.settings.target_browsers,
                'target_placements': ad_group.settings.target_placements,
                'target_regions': ad_group.settings.target_regions,
                'exclusion_target_regions': ad_group.settings.exclusion_target_regions,
                'iab_category': ad_group.campaign.settings.iab_category,
                'campaign_language': ad_group.campaign.settings.language,
                'retargeting': self._get_retargeting(ad_group.settings),
                'demographic_targeting': ad_group.settings.bluekai_targeting,
                'interest_targeting': ad_group.settings.interest_targeting,
                'exclusion_interest_targeting': ad_group.settings.exclusion_interest_targeting,
                'campaign_id': ad_group.campaign.id,
                'campaign_name': ad_group.campaign.name,
                'account_id': ad_group.campaign.account.id,
                'account_name': ad_group.campaign.account.name,
                'agency_id': ad_group.campaign.account.agency_id,
                'agency_name': agency_name,
                'goal_types': campaign_goal_types[ad_group.campaign.id],
                'goals': campaign_goals[ad_group.campaign.id],
                'dayparting': ad_group.settings.dayparting,
                'max_cpm': format(max_cpm, '.4f') if max_cpm else max_cpm,
                'b1_sources_group': {
                    'enabled': ad_group.settings.b1_sources_group_enabled,
                    'daily_budget': b1_sources_group_daily_budget,
                    'cpc_cc': b1_sources_group_cpc_cc,
                    'state': ad_group.settings.b1_sources_group_state,
                },
                'whitelist_publisher_groups': whitelist,
                'blacklist_publisher_groups': blacklist,
                'delivery_type': ad_group.settings.delivery_type,
                'click_capping_daily_ad_group_max_clicks': ad_group.settings.click_capping_daily_ad_group_max_clicks,
                'click_capping_daily_click_budget': ad_group.settings.click_capping_daily_click_budget,
                'custom_flags': flags,
                'amplify_review': ad_group.amplify_review,
            }

            ad_group_dicts.append(ad_group_dict)

        return self.response_ok(ad_group_dicts)

    @staticmethod
    def _get_retargeting(ad_group_settings):
        retargeting = []

        for retargeting_ad_group_id in ad_group_settings.retargeting_ad_groups:
            retargeting.append(
                {'event_type': EVENT_RETARGET_ADGROUP, 'event_id': str(retargeting_ad_group_id), 'exclusion': False})

        for retargeting_ad_group_id in ad_group_settings.exclusion_retargeting_ad_groups:
            retargeting.append(
                {'event_type': EVENT_RETARGET_ADGROUP, 'event_id': str(retargeting_ad_group_id), 'exclusion': True})

        for audience_id in ad_group_settings.audience_targeting:
            retargeting.append({'event_type': EVENT_CUSTOM_AUDIENCE, 'event_id': str(audience_id), 'exclusion': False})

        for audience_id in ad_group_settings.exclusion_audience_targeting:
            retargeting.append({'event_type': EVENT_CUSTOM_AUDIENCE, 'event_id': str(audience_id), 'exclusion': True})

        return retargeting

    @staticmethod
    def _get_end_date(ad_group_settings, campaignstop_states):
        campaign = ad_group_settings.ad_group.campaign
        max_allowed_end_date = campaignstop_states.get(campaign.id, {}).get('max_allowed_end_date')
        if max_allowed_end_date is None:
            return ad_group_settings.end_date

        if ad_group_settings.end_date is None:
            return max_allowed_end_date

        return min(ad_group_settings.end_date, max_allowed_end_date)

    @staticmethod
    def _get_campaign_goal_types(campaign_ids):
        '''
        returns a map campaign_id:[goal_type,...]
        the first element in the list is the type of the primary goal
        '''
        campaign_goals = {cid: [] for cid in campaign_ids}
        for goal in dash.models.CampaignGoal.objects.filter(campaign__in=campaign_ids):
            campaign_goals[goal.campaign_id].append((goal.primary, goal.type))
        for cid in list(campaign_goals.keys()):
            campaign_goals[cid] = [tup[1] for tup in sorted(campaign_goals[cid], reverse=True)]
        return campaign_goals

    @staticmethod
    def _get_campaign_goals(campaign_ids):
        '''
        returns a map campaign_id:[goals_dict,...]
        the first element in the list is the type of the primary goal
        '''
        campaign_goals = {cid: [] for cid in campaign_ids}
        for goal in dash.models.CampaignGoal.objects.filter(campaign__in=campaign_ids).select_related('conversion_goal').prefetch_related('values'):
            campaign_goals[goal.campaign_id].append(goal)

        campaign_goals_dicts = {}
        for cid, goals in campaign_goals.items():
            sorted_goals = sorted(goals, key=lambda x: (x.primary, x.pk), reverse=True)
            campaign_goals_dicts[cid] = [
                goal.to_dict(with_values=True) for goal in sorted_goals
            ]
        return campaign_goals_dicts

    @staticmethod
    def _get_ad_groups(ad_group_ids, source_types, slugs, marker, limit):
        ad_groups = dash.models.AdGroup.objects.all()

        if ad_group_ids:
            ad_groups = ad_groups.filter(pk__in=ad_group_ids)
        if marker:
            ad_groups = ad_groups.filter(pk__gt=int(marker))

        if source_types or slugs:
            ad_group_sources = dash.models.AdGroupSource.objects.filter(ad_group__in=ad_groups)
            if source_types:
                ad_group_sources = ad_group_sources.filter(source__source_type__type__in=source_types)
            if slugs:
                ad_group_sources = ad_group_sources.filter(source__bidder_slug__in=slugs)
            ad_groups = ad_groups.filter(pk__in=ad_group_sources.values('ad_group_id'))

        ad_groups = ad_groups.exclude_archived()

        # apply pagination
        ad_groups = ad_groups.order_by('pk')[:limit]

        ad_groups = ad_groups.select_related(
            'settings',
            'campaign__settings',
            'campaign__account__settings',
            'campaign__account__agency__settings',
        )

        campaignstop_states = automation.campaignstop.get_campaignstop_states(
            set(ad_group.campaign for ad_group in ad_groups))

        budgets = (dash.models.BudgetLineItem.objects
                   .filter(campaign_id__in=set([ad_group.campaign_id for ad_group in ad_groups]))
                   .filter_today()
                   .distinct('campaign_id')
                   .select_related('credit', 'campaign')
                   )
        campaigns_budgets_map = {
            budget.campaign_id: budget for budget in budgets
        }

        return ad_groups,\
            campaigns_budgets_map,\
            campaignstop_states
