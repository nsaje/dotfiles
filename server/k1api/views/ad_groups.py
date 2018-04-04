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

    Filterable by ad_group_id, source_type and slug.
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

        ad_groups_settings,\
            campaigns_settings_map,\
            accounts_settings_map,\
            agencies_settings_map,\
            campaigns_budgets_map,\
            campaignstop_states = self._get_settings_maps(ad_group_ids, source_types, slugs, marker, limit)

        campaign_goal_types = self._get_campaign_goal_types(list(campaigns_settings_map.keys()))
        campaign_goals = self._get_campaign_goals(list(campaigns_settings_map.keys()))

        all_custom_flags = {
            flag: False
            for flag in dash.features.custom_flags.CustomFlag.objects.all().values_list(
                'id', flat=True
            )
        }

        ad_groups = []
        for ad_group_settings in ad_groups_settings:
            if ad_group_settings is None:
                logger.error('K1API - ad group settings are None')
                continue

            campaign_settings = campaigns_settings_map[ad_group_settings.ad_group.campaign_id]
            account_settings = accounts_settings_map[ad_group_settings.ad_group.campaign.account_id]
            agency_settings = agencies_settings_map.get(ad_group_settings.ad_group.campaign.account.agency_id)  # FIXME(nsaje): settings should exist

            blacklist = ad_group_settings.blacklist_publisher_groups
            whitelist = ad_group_settings.whitelist_publisher_groups

            ad_group = ad_group_settings.ad_group
            blacklist, whitelist = publisher_group_helpers.concat_publisher_group_targeting(
                ad_group, ad_group_settings,
                ad_group.campaign, campaign_settings,
                ad_group.campaign.account, account_settings,
                ad_group.campaign.account.agency, agency_settings,
                include_global=False  # global blacklist is handled separately by the bidder, no need to duplicate work
            )

            license_fee = None
            margin = None
            if ad_group.campaign_id in campaigns_budgets_map:
                license_fee = campaigns_budgets_map[ad_group.campaign_id].credit.license_fee
                margin = campaigns_budgets_map[ad_group.campaign_id].margin

            max_cpm = ad_group_settings.get_external_max_cpm(
                ad_group.campaign.account,
                license_fee,
                margin
            )
            b1_sources_group_daily_budget = ad_group_settings.get_external_b1_sources_group_daily_budget(
                ad_group.campaign.account,
                license_fee,
                margin
            )
            b1_sources_group_cpc_cc = ad_group_settings.get_external_b1_sources_group_cpc_cc(
                ad_group.campaign.account,
                license_fee,
                margin,
            )

            # FIXME: k1 doesn't update missing keys, find a better solution
            flags = {}
            flags.update(all_custom_flags)
            flags.update(ad_group.get_all_custom_flags())

            ad_group = {
                'id': ad_group.id,
                'name': ad_group.get_external_name(),
                'start_date': ad_group_settings.start_date,
                'end_date': self._get_end_date(ad_group_settings, campaignstop_states),
                'time_zone': settings.DEFAULT_TIME_ZONE,
                'brand_name': ad_group_settings.brand_name,
                'display_url': ad_group_settings.display_url,
                'tracking_codes': ad_group_settings.get_tracking_codes(),
                'target_devices': ad_group_settings.target_devices,
                'target_os': ad_group_settings.target_os,
                'target_browsers': ad_group_settings.target_browsers,
                'target_placements': ad_group_settings.target_placements,
                'target_regions': ad_group_settings.target_regions,
                'exclusion_target_regions': ad_group_settings.exclusion_target_regions,
                'iab_category': campaign_settings.iab_category,
                'campaign_language': campaign_settings.language,
                'retargeting': self._get_retargeting(ad_group_settings),
                'demographic_targeting': ad_group_settings.bluekai_targeting,
                'interest_targeting': ad_group_settings.interest_targeting,
                'exclusion_interest_targeting': ad_group_settings.exclusion_interest_targeting,
                'campaign_id': ad_group.campaign.id,
                'account_id': ad_group.campaign.account.id,
                'agency_id': ad_group.campaign.account.agency_id,
                'goal_types': campaign_goal_types[ad_group.campaign.id],
                'goals': campaign_goals[ad_group.campaign.id],
                'dayparting': ad_group_settings.dayparting,
                'max_cpm': format(max_cpm, '.4f') if max_cpm else max_cpm,
                'b1_sources_group': {
                    'enabled': ad_group_settings.b1_sources_group_enabled,
                    'daily_budget': b1_sources_group_daily_budget,
                    'cpc_cc': b1_sources_group_cpc_cc,
                    'state': ad_group_settings.b1_sources_group_state,
                },
                'whitelist_publisher_groups': whitelist,
                'blacklist_publisher_groups': blacklist,
                'delivery_type': ad_group_settings.delivery_type,
                'click_capping_daily_ad_group_max_clicks': ad_group_settings.click_capping_daily_ad_group_max_clicks,
                'click_capping_daily_click_budget': ad_group_settings.click_capping_daily_click_budget,
                'custom_flags': flags,
            }

            ad_groups.append(ad_group)

        return self.response_ok(ad_groups)

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
    def _get_settings_maps(ad_group_ids, source_types, slugs, marker, limit):
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

        ad_groups_settings = (dash.models.AdGroupSettings.objects
                              .filter(ad_group__in=ad_groups)
                              .select_related('ad_group__campaign__account__agency')
                              .order_by('ad_group_id')
                              .group_current_settings())

        campaigns_settings = (dash.models.CampaignSettings.objects
                              .filter(campaign_id__in=set([ag.ad_group.campaign_id for ag in ad_groups_settings]))
                              .group_current_settings()
                              .only('campaign_id', 'iab_category', 'whitelist_publisher_groups', 'blacklist_publisher_groups'))
        campaigns_settings_map = {cs.campaign_id: cs for cs in campaigns_settings}
        campaignstop_states = automation.campaignstop.get_campaignstop_states(
            set(ad_group_settings.ad_group.campaign for ad_group_settings in ad_groups_settings))

        accounts_settings = (dash.models.AccountSettings.objects
                             .filter(account_id__in=set([ag.ad_group.campaign.account_id for ag in ad_groups_settings]))
                             .group_current_settings()
                             .only('account_id', 'whitelist_publisher_groups', 'blacklist_publisher_groups'))
        accounts_settings_map = {accs.account_id: accs for accs in accounts_settings}

        agencies_settings = (dash.models.AgencySettings.objects
                             .filter(agency_id__in=set([ag.ad_group.campaign.account.agency_id for ag in ad_groups_settings]))
                             .group_current_settings()
                             .only('agency_id', 'whitelist_publisher_groups', 'blacklist_publisher_groups'))
        agencies_settings_map = {agncs.agency_id: agncs for agncs in agencies_settings}

        budgets = (dash.models.BudgetLineItem.objects
                   .filter(campaign_id__in=set([ag.ad_group.campaign_id for ag in ad_groups_settings]))
                   .filter_today()
                   .distinct('campaign_id')
                   .select_related('credit', 'campaign')
                   )
        campaigns_budgets_map = {
            budget.campaign_id: budget for budget in budgets
        }

        return ad_groups_settings,\
            campaigns_settings_map,\
            accounts_settings_map,\
            agencies_settings_map,\
            campaigns_budgets_map,\
            campaignstop_states
