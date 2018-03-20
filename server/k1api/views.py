import json
import logging
import time
from collections import defaultdict
import datetime
import uuid

import influx
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse, Http404
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

import dash.constants
import dash.models
from dash import constants
from core.publisher_groups import publisher_group_helpers
from utils import redirector_helper, email_helper
from utils import url_helper, request_signer, converters
from utils import db_for_reads
from utils import influx_helper
import redshiftapi.api_quickstats
import redshiftapi.internal_stats.conversions
import redshiftapi.internal_stats.content_ad_publishers
import etl.materialize_views
import dash.features.geolocation
import dash.features.ga
import dash.features.custom_flags
import dash.features.submission_filters
import core.publisher_bid_modifiers
import automation.campaignstop.service

logger = logging.getLogger(__name__)

EVENT_RETARGET_ADGROUP = "redirect_adgroup"
EVENT_CUSTOM_AUDIENCE = "aud"

BLOCKED_AGENCIES = (151, 165, )
BLOCKED_ACCOUNTS = (523, )


class K1APIView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        self._validate_signature(request)
        start_time = time.time()
        response = super(K1APIView, self).dispatch(request, *args, **kwargs)
        influx.timing(
            'k1api.request',
            (time.time() - start_time),
            endpoint=self.__class__.__name__,
            path=influx_helper.clean_path(request.path),
            method=request.method,
            status=str(response.status_code),
        )
        return response

    @staticmethod
    def _validate_signature(request):
        try:
            request_signer.verify_wsgi_request(request, settings.K1_API_SIGN_KEY + settings.BIDDER_API_SIGN_KEY)
        except request_signer.SignatureError:
            logger.exception('Invalid K1 signature.')
            raise Http404

    @staticmethod
    def response_ok(content):
        return JsonResponse({
            "error": None,
            "response": content,
        })

    @staticmethod
    def response_error(msg, status=400):
        return JsonResponse({
            "error": msg,
            "response": None,
        }, status=status)


class AccountsView(K1APIView):

    @db_for_reads.use_read_replica()
    def get(self, request):
        account_ids = request.GET.get('account_ids')
        accounts = (dash.models.Account.objects
                    .all()
                    .exclude_archived()
                    .prefetch_related('conversionpixel_set',
                                      'conversionpixel_set__sourcetypepixel_set',
                                      'conversionpixel_set__sourcetypepixel_set__source_type'))
        if account_ids:
            accounts = accounts.filter(id__in=account_ids.split(','))

        accounts_audiences = self._get_audiences_for_accounts(accounts)
        account_dicts = []
        for account in accounts:
            pixels = []
            for pixel in account.conversionpixel_set.all().order_by('pk'):
                if pixel.archived:
                    continue

                source_pixels = []
                for source_pixel in pixel.sourcetypepixel_set.all().order_by('pk'):
                    source_pixel_dict = {
                        'url': source_pixel.url,
                        'source_pixel_id': source_pixel.source_pixel_id,
                        'source_type': source_pixel.source_type.type,
                    }
                    source_pixels.append(source_pixel_dict)

                pixel_dict = {
                    'id': pixel.id,
                    'name': pixel.name,
                    'slug': pixel.slug,
                    'audience_enabled': pixel.audience_enabled,
                    'additional_pixel': pixel.additional_pixel,
                    'source_pixels': source_pixels,
                }
                pixels.append(pixel_dict)

            account_dict = {
                'id': account.id,
                'name': account.name,
                'pixels': pixels,
                'custom_audiences': accounts_audiences[account.id],
                'outbrain_marketer_id': account.outbrain_marketer_id,
            }
            account_dicts.append(account_dict)

        return self.response_ok(account_dicts)

    def _get_audiences_for_accounts(self, accounts):
        accounts_audiences = defaultdict(list)
        audiences = (dash.models.Audience.objects
                     .filter(pixel__account__in=accounts, archived=False)
                     .select_related('pixel')
                     .prefetch_related('audiencerule_set')
                     .order_by('pk'))
        for audience in audiences:
            rules = []
            for rule in audience.audiencerule_set.all().order_by('pk'):
                rule_dict = {
                    'id': rule.id,
                    'type': rule.type,
                    'values': rule.value,
                }
                rules.append(rule_dict)

            audience_dict = {
                'id': audience.id,
                'name': audience.name,
                'pixel_id': audience.pixel.id,
                'ttl': audience.ttl,
                'rules': rules,
            }
            accounts_audiences[audience.pixel.account_id].append(audience_dict)
        return accounts_audiences


class SourcesView(K1APIView):

    @db_for_reads.use_read_replica()
    def get(self, request):
        source_slugs = request.GET.get("source_slugs")
        sources = dash.models.Source.objects.all().select_related('defaultsourcesettings',
                                                                  'defaultsourcesettings__credentials')
        if source_slugs:
            sources = sources.filter(bidder_slug__in=source_slugs.split(','))

        response = []
        for source in sources:
            source_dict = {
                'id': source.id,
                'slug': source.tracking_slug,
                'credentials': None
            }
            try:
                default_credentials = source.defaultsourcesettings.credentials
                if default_credentials:
                    source_dict['credentials'] = {
                        'id': default_credentials.id,
                        'credentials': default_credentials.credentials
                    }
            except dash.models.DefaultSourceSettings.DoesNotExist:
                pass
            response.append(source_dict)
        return self.response_ok(response)


class SourcePixelsView(K1APIView):

    @transaction.atomic
    def put(self, request):
        data = json.loads(request.body)
        pixel_id = data['pixel_id']
        source_type = data['source_type']

        conversion_pixel = dash.models.ConversionPixel.objects.get(id=pixel_id)

        if source_type == 'outbrain':
            self._update_outbrain_pixel(conversion_pixel.account, data)
        else:
            self._create_source_pixel(conversion_pixel, source_type, data)
            self._propagate_pixels_to_r1(pixel_id)

        return self.response_ok(data)

    def _propagate_pixels_to_r1(self, pixel_id):
        audiences = dash.models.Audience.objects.filter(pixel_id=pixel_id, archived=False)

        for audience in audiences:
            redirector_helper.upsert_audience(audience)

    def _create_source_pixel(self, conversion_pixel, source_type, data):
        source_pixel, created = dash.models.SourceTypePixel.objects.get_or_create(
            pixel__id=conversion_pixel.id,
            source_type__type=source_type,
            defaults={
                'pixel': conversion_pixel,
                'source_type': dash.models.SourceType.objects.get(type=source_type),
            })

        source_pixel.url = data['url']
        source_pixel.source_pixel_id = data['source_pixel_id']
        source_pixel.save()

    def _update_outbrain_pixel(self, account, data):
        pixels = dash.models.ConversionPixel.objects.\
            filter(account_id=account.id).\
            filter(audience_enabled=True)
        if not pixels:
            return

        if len(pixels) > 1:
            msg = 'More than 1 pixel enabled for audience building for account {}'.format(account.id)
            return self.response_error(msg)

        conversion_pixel = pixels[0]
        r1_pixels_to_sync = []

        source_type_pixels = dash.models.SourceTypePixel.objects.filter(
            pixel__account=account, source_type__type=constants.SourceType.OUTBRAIN
        )
        if len(source_type_pixels) > 1:
            return self.response_error('More than 1 outbrain source type pixel for account {}'.format(account.id))

        if not source_type_pixels:
            self._create_source_pixel(conversion_pixel, 'outbrain', data)
            r1_pixels_to_sync.append(conversion_pixel.id)
        elif source_type_pixels[0].pixel != conversion_pixel:
            r1_pixels_to_sync.append(conversion_pixel.id)
            r1_pixels_to_sync.append(source_type_pixels[0].pixel.id)

            source_type_pixels[0].pixel = conversion_pixel
            source_type_pixels[0].save()

        # sync all audiences on edited pixels with R1
        for pixel_id in r1_pixels_to_sync:
            self._propagate_pixels_to_r1(pixel_id)


class GAAccountsView(K1APIView):

    @db_for_reads.use_read_replica()
    def get(self, request):
        date_since = request.GET.get('date_since')

        all_active_campaign_ids = set(dash.models.Campaign.objects.all(
        ).exclude_archived().values_list('id', flat=True))
        if 'campaigns' in request.GET:
            all_active_campaign_ids = set(request.GET.get('campaigns', '').split(','))
        all_current_settings = dash.models.CampaignSettings.objects.filter(
            campaign_id__in=all_active_campaign_ids
        ).group_current_settings()
        ga_accounts = set()
        for current_settings in all_current_settings:
            self._extract_ga_settings(ga_accounts, current_settings)
        if date_since:
            valid_previous_settings = dash.models.CampaignSettings.objects.filter(
                campaign_id__in=all_active_campaign_ids,
                created_dt__lte=datetime.datetime.strptime(date_since, '%Y-%m-%d').date()
            ).order_by('campaign_id', '-created_dt').distinct('campaign')
            for previous_settings in valid_previous_settings:
                self._extract_ga_settings(ga_accounts, previous_settings)
            all_intermediate_settings = dash.models.CampaignSettings.objects.filter(
                campaign_id__in=all_active_campaign_ids,
                created_dt__gte=datetime.datetime.strptime(date_since, '%Y-%m-%d').date()
            ).exclude(
                pk__in=set(s.pk for s in all_current_settings) | set(s.pk for s in valid_previous_settings)
            ).exclude(
                ga_property_id__in=set(ga_property_id for _, _, ga_property_id in ga_accounts)
            )
            for previous_settings in all_intermediate_settings:
                self._extract_ga_settings(ga_accounts, previous_settings)
        ga_accounts_dicts = [
            {'account_id': account_id, 'ga_account_id': ga_account_id, 'ga_web_property_id': ga_web_property_id}
            for account_id, ga_account_id, ga_web_property_id in sorted(ga_accounts)
        ]
        ga_account_ids = set(ga_account_id for _, ga_account_id, _ in ga_accounts)

        return self.response_ok({
            'ga_accounts': list(ga_accounts_dicts),
            'service_email_mapping': self._get_service_email_mapping(ga_account_ids)
        })

    def _extract_ga_settings(self, ga_accounts, campaign_settings):
        if not (campaign_settings.enable_ga_tracking and
                campaign_settings.ga_tracking_type == dash.constants.GATrackingType.API and
                campaign_settings.ga_property_id):
            return
        ga_property_id = campaign_settings.ga_property_id
        ga_accounts.add((
            campaign_settings.campaign.account_id,
            dash.features.ga.extract_ga_account_id(ga_property_id),
            ga_property_id
        ))

    def _get_service_email_mapping(self, ga_account_ids):
        mapping = {
            m.customer_ga_account_id: m.zem_ga_account_email
            for m in dash.features.ga.GALinkedAccounts.objects.filter(customer_ga_account_id__in=ga_account_ids)
        }
        # TODO: sigi 8.2.2018
        # both zem users have access to the same profile but only one is reciving data
        if '5428971' in mapping:
            mapping['5428971'] = 'account-1@zemanta-api.iam.gserviceaccount.com'
        return mapping


class R1MappingView(K1APIView):

    @db_for_reads.use_read_replica()
    def get(self, request):
        accounts = [int(account) for account in request.GET.getlist('account')]

        data = {account: {'slugs': [], 'ad_groups': {}} for account in accounts}

        conversion_pixels = (dash.models.ConversionPixel.objects
                             .filter(account_id__in=accounts)
                             .filter(archived=False))
        for conversion_pixel in conversion_pixels:
            data[conversion_pixel.account_id]['slugs'].append(conversion_pixel.slug)

        ad_groups = (dash.models.AdGroup.objects.all()
                     .exclude_archived()
                     .select_related('campaign')
                     .filter(campaign__account_id__in=accounts))
        for ad_group in ad_groups:
            data[ad_group.campaign.account_id]['ad_groups'][ad_group.id] = {
                'campaign_id': ad_group.campaign_id,
            }

        return self.response_ok(data)


class OutbrainPublishersBlacklistView(K1APIView):

    @db_for_reads.use_read_replica()
    def get(self, request):
        marketer_id = request.GET.get('marketer_id')
        account = {}
        blacklisted_publishers = []
        for acc in dash.models.Account.objects.filter(outbrain_marketer_id=marketer_id):
            # NOTE(sigi): sadly, we have some accounts with the same marketer id
            if acc.is_archived():
                continue
            account = {
                'id': acc.id,
                'name': acc.name,
                'outbrain_marketer_id': acc.outbrain_marketer_id,
            }
            current_settings = acc.get_current_settings()
            blacklisted_publishers = (
                dash.models.PublisherGroupEntry.objects
                    .filter(publisher_group_id__in=(current_settings.blacklist_publisher_groups + [acc.default_blacklist_id]))
                    .filter(source__bidder_slug='outbrain')
                    .annotate(name=F('publisher'))
                    .values('name')
            )
        return self.response_ok({
            'blacklist': list(blacklisted_publishers),
            'account': account
        })


class PublisherGroupsView(K1APIView):

    @db_for_reads.use_read_replica()
    def get(self, request):
        account_id = request.GET.get('account_id')

        publisher_groups = dash.models.PublisherGroup.objects.all()
        if account_id:
            publisher_groups = publisher_groups.filter_by_account(
                dash.models.Account.objects.get(pk=account_id))

        return self.response_ok(list(publisher_groups.values(
            'id',
            'account_id'
        )))


class PublisherGroupsEntriesView(K1APIView):

    @db_for_reads.use_read_replica()
    def get(self, request):
        account_id = request.GET.get('account_id')
        source_slug = request.GET.get('source_slug')
        offset = request.GET.get('offset') or 0
        limit = request.GET.get('limit')

        if not limit:
            return self.response_error('Limit parameter is missing', status=400)
        offset = int(offset)
        limit = int(limit)

        # ensure unique order
        entries = dash.models.PublisherGroupEntry.objects.all().order_by('pk')
        if account_id:
            publisher_groups = dash.models.PublisherGroup.objects.all().filter_by_account(
                dash.models.Account.objects.get(pk=account_id))
            entries = entries.filter(publisher_group__in=publisher_groups)

        if source_slug:
            entries = entries.filter(source__bidder_slug=source_slug)

        return self.response_ok(list(entries[offset:offset + limit].annotate(
            source_slug=F('source__bidder_slug'),
            account_id=F('publisher_group__account_id'),
        ).values('source_slug', 'publisher_group_id', 'include_subdomains', 'outbrain_publisher_id',
                 'outbrain_section_id', 'outbrain_amplify_publisher_id', 'outbrain_engage_publisher_id', 'publisher', 'account_id')))


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


class AdGroupStatsView(K1APIView):
    """
    Returns quickstats for an adgroup (used for decision making based on whether the ad group has spent already)
    """

    @db_for_reads.use_read_replica()
    def get(self, request):
        ad_group_id = request.GET.get('ad_group_id')
        source_slug = request.GET.get('source_slug')
        ad_group = dash.models.AdGroup.objects.get(pk=ad_group_id)
        try:
            source = dash.models.Source.objects.get(bidder_slug=source_slug)
        except dash.models.Source.DoesNotExist:
            return self.response_error('Source \'{}\' does not exist'.format(source_slug), status=400)
        from_date = ad_group.created_dt.date()
        to_date = datetime.date.today() + datetime.timedelta(days=1)
        stats = redshiftapi.api_quickstats.query_adgroup(ad_group.id, from_date, to_date, source.id)
        return self.response_ok({
            'total_cost': stats['total_cost'],
            'impressions': stats['impressions'],
            'clicks': stats['clicks'],
            'cpc': stats['cpc'],
        })


class AdGroupConversionStatsView(K1APIView):
    """
    Returns conversion stats for an adgroup (used for post kpi optimization in bidder)
    """

    def get(self, request):
        try:
            from_date = datetime.datetime.strptime(request.GET.get('from_date'), '%Y-%m-%d').date()
            to_date = datetime.datetime.strptime(request.GET.get('to_date'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return self.response_error('Invalid date format', status=400)

        ad_group_ids = request.GET.get('ad_group_ids')
        if ad_group_ids:
            ad_group_ids = ad_group_ids.split(',')

        path = etl.materialize_views.upload_csv(
            "conversions",
            from_date,
            uuid.uuid4().hex,
            lambda: redshiftapi.internal_stats.conversions.query_conversions(
                from_date, to_date, ad_group_ids),
        )

        return self.response_ok({
            'path': path,
            'bucket': settings.S3_BUCKET_STATS,
        })


class AdGroupContentAdPublisherStatsView(K1APIView):
    """
    Returns conversion stats for an adgroup (used for post kpi optimization in bidder)
    """

    def get(self, request):
        try:
            from_date = datetime.datetime.strptime(request.GET.get('from_date'), '%Y-%m-%d').date()
            to_date = datetime.datetime.strptime(request.GET.get('to_date'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return self.response_error('Invalid date format', status=400)

        ad_group_ids = request.GET.get('ad_group_ids')
        if ad_group_ids:
            ad_group_ids = ad_group_ids.split(',')

        min_media_cost = request.GET.get('min_media_cost')
        if min_media_cost:
            min_media_cost = float(min_media_cost)

        _, path = etl.materialize_views.upload_csv_async(
            "content_ad_publishers",
            from_date,
            uuid.uuid4().hex,
            lambda: redshiftapi.internal_stats.content_ad_publishers.query_content_ad_publishers(
                from_date, to_date, ad_group_ids, min_media_cost),
        )

        return self.response_ok({
            'path': path,
            'bucket': settings.S3_BUCKET_STATS,
        })


class AdGroupSourcesView(K1APIView):

    @db_for_reads.use_read_replica()
    def get(self, request):
        """
        Returns a list of non-archived ad group sources together with their current source settings.

        Filterable by ad_group_id, source_type and slug.
        """
        ad_group_ids = request.GET.get('ad_group_ids')
        source_types = request.GET.get('source_types')
        slugs = request.GET.get('source_slugs')
        if ad_group_ids:
            ad_group_ids = ad_group_ids.split(',')
        if source_types:
            source_types = source_types.split(',')
        if slugs:
            slugs = slugs.split(',')

        # get ad groups we're interested in
        ad_groups = dash.models.AdGroup.objects.all()
        if ad_group_ids:
            ad_groups = ad_groups.filter(id__in=ad_group_ids)
        ad_groups = ad_groups.exclude_archived()
        ad_group_ids = list(ad_groups.values_list('id', flat=True))

        campaigns = dash.models.Campaign.objects.filter(adgroup__in=ad_groups)
        campaignstop_map = automation.campaignstop.get_campaignstop_states(campaigns)

        ad_groups_settings_query = dash.models.AdGroupSettings.objects.filter(ad_group__in=ad_group_ids)
        ad_groups_settings = ad_groups_settings_query.group_current_settings()

        ad_group_settings_map = {ags.ad_group_id: ags for ags in ad_groups_settings}

        ag_source_settings_query = (dash.models.AdGroupSourceSettings.objects
                                    .filter(ad_group_source__ad_group__in=list(ad_group_settings_map.keys()))
                                    .filter(ad_group_source__source__deprecated=False))

        # filter which sources we want
        if source_types:
            ag_source_settings_query = ag_source_settings_query.filter(
                ad_group_source__source__source_type__type__in=source_types)
        if slugs:
            ag_source_settings_query = ag_source_settings_query.filter(
                ad_group_source__source__bidder_slug__in=slugs)

        ad_group_source_settings = (ag_source_settings_query
                                    .group_current_settings()
                                    .select_related('ad_group_source__source__source_type',
                                                    'ad_group_source__ad_group__campaign__account'))

        # build a map of today's campaign budgets
        budgets = dash.models.BudgetLineItem.objects.all().filter_today().distinct('campaign_id').select_related('credit')
        if ad_group_ids:
            budgets = budgets.filter(campaign__adgroup__in=ad_group_ids)
        campaigns_budgets_map = {
            budget.campaign_id: budget for budget in budgets
        }

        # build the list of objects
        ad_group_sources = []
        for ad_group_source_settings in ad_group_source_settings:
            ad_group = ad_group_source_settings.ad_group_source.ad_group
            ad_group_settings = ad_group_settings_map[ad_group.id]
            campaignstop_allowed_to_run = campaignstop_map[ad_group.campaign.id]['allowed_to_run']
            if self._is_ad_group_source_enabled(
                    ad_group_settings,
                    ad_group_source_settings,
                    campaignstop_allowed_to_run):
                source_state = constants.AdGroupSettingsState.ACTIVE
            else:
                source_state = constants.AdGroupSettingsState.INACTIVE
            # NOTE(nsaje): taking adgroupsource.blockers into account here is not necessary, since the
            # executor should know when it has a blocking action pending

            tracking_code = url_helper.combine_tracking_codes(
                ad_group_settings.get_tracking_codes(), ''
            )

            campaign = ad_group_source_settings.ad_group_source.ad_group.campaign

            license_fee = None
            margin = None
            if campaign.id in campaigns_budgets_map:
                license_fee = campaigns_budgets_map[campaign.id].credit.license_fee
                margin = campaigns_budgets_map[campaign.id].margin

            cpc_cc = ad_group_source_settings.get_external_cpc_cc(
                campaign.account,
                license_fee,
                margin,
            )
            daily_budget_cc = ad_group_source_settings.get_external_daily_budget_cc(
                campaign.account,
                license_fee,
                margin,
            )

            if (ad_group.campaign.account.agency_id in BLOCKED_AGENCIES or
                    ad_group.campaign.account_id in BLOCKED_ACCOUNTS):
                source_state = constants.AdGroupSettingsState.INACTIVE
            source = {
                'ad_group_id': ad_group_settings.ad_group_id,
                'slug': ad_group_source_settings.ad_group_source.source.bidder_slug,
                'source_campaign_key': ad_group_source_settings.ad_group_source.source_campaign_key,
                'tracking_code': tracking_code,
                'state': source_state,
                'cpc_cc': format(cpc_cc, '.4f'),
                'daily_budget_cc': format(daily_budget_cc, '.4f'),
            }
            ad_group_sources.append(source)

        return self.response_ok(ad_group_sources)

    def _is_ad_group_source_enabled(self, ad_group_settings, ad_group_source_settings, campaignstop_allowed_to_run):
        if not campaignstop_allowed_to_run:
            return False

        if ad_group_settings.state != constants.AdGroupSettingsState.ACTIVE:
            return False

        if ad_group_source_settings.state != constants.AdGroupSourceSettingsState.ACTIVE:
            return False

        if (ad_group_source_settings.ad_group_source.source.source_type.type == constants.SourceType.B1 and
                ad_group_settings.b1_sources_group_enabled and
                ad_group_settings.b1_sources_group_state != constants.AdGroupSourceSettingsState.ACTIVE):
            return False

        return True

    def put(self, request):
        """
        Updates ad group source settings.
        """
        ad_group_id = request.GET.get('ad_group_id')
        bidder_slug = request.GET.get('source_slug')
        data = json.loads(request.body)

        if not (ad_group_id and bidder_slug and data):
            return self.response_error("Must provide ad_group_id, source_slug and conf", status=404)

        try:
            ad_group_source = dash.models.AdGroupSource.objects.get(ad_group__id=ad_group_id,
                                                                    source__bidder_slug=bidder_slug)
        except dash.models.AdGroupSource.DoesNotExist:
            return self.response_error(
                "No AdGroupSource exists for ad_group_id: %s with bidder_slug %s" % (ad_group_id, bidder_slug),
                status=404)
        ad_group_source_settings = ad_group_source.get_current_settings()
        new_settings = ad_group_source_settings.copy_settings()

        settings_changed = False
        for key, val in list(data.items()):
            if key == 'cpc_cc':
                logger.error('K1API - unexpected update of ad group source cpc_cc')
                new_settings.cpc_cc = converters.cc_to_decimal(val)
                settings_changed = True
            elif key == 'daily_budget_cc':
                logger.error('K1API - unexpected update of ad group source daily_budget_cc')
                new_settings.daily_budget_cc = converters.cc_to_decimal(val)
                settings_changed = True
            elif key == 'state':
                new_settings.state = val
                settings_changed = True
            elif key == 'source_campaign_key':
                if ad_group_source.source_campaign_key and val != ad_group_source.source_campaign_key:
                    return self.response_error("Cannot change existing source_campaign_key", status=400)
                ad_group_source.source_campaign_key = val
                ad_group_source.save()
            else:
                return self.response_error("Invalid setting!", status=400)

        if settings_changed:
            new_settings.save(None, system_user=dash.constants.SystemUserType.K1_USER)
        return self.response_ok([])


class AdGroupSourceBlockersView(K1APIView):

    def put(self, request):
        """
        Add/remove a blocker of an ad group source.
        """
        ad_group_id = request.GET.get('ad_group_id')
        source_slug = request.GET.get('source_slug')
        ad_group_source = dash.models.AdGroupSource.objects.only('blockers').get(
            ad_group_id=ad_group_id, source__bidder_slug=source_slug)

        blockers_update = json.loads(request.body)
        changes = 0
        for key, value in list(blockers_update.items()):
            if not (isinstance(key, str) and (isinstance(value, str) or value is None)):
                return self.response_error("Bad input: blocker key should be string and value should be either string or None", status=400)
            if value and value != ad_group_source.blockers.get(key):
                ad_group_source.blockers[key] = value
                changes += 1
            if not value and key in ad_group_source.blockers:
                del ad_group_source.blockers[key]
                changes += 1

        if changes:
            ad_group_source.save()
        return self.response_ok(ad_group_source.blockers)


class ContentAdsView(K1APIView):

    @db_for_reads.use_read_replica()
    def get(self, request):
        content_ad_ids = request.GET.get('content_ad_ids')
        ad_group_ids = request.GET.get('ad_group_ids')
        include_archived = request.GET.get('include_archived') == 'True'

        content_ads = dash.models.ContentAd.objects.all()
        if not include_archived:
            content_ads = content_ads.exclude_archived()
            nonarchived_ad_groups = dash.models.AdGroup.objects.all().exclude_archived()
            content_ads.filter(ad_group__in=nonarchived_ad_groups)
        if content_ad_ids:
            content_ad_ids = content_ad_ids.split(',')
            content_ads = content_ads.filter(id__in=content_ad_ids)
        if ad_group_ids:
            ad_group_ids = ad_group_ids.split(',')
            content_ads = content_ads.filter(ad_group_id__in=ad_group_ids)
        content_ads = content_ads.select_related('ad_group', 'ad_group__campaign', 'ad_group__campaign__account')
        campaign_settings_map = {
            cs.campaign_id: cs
            for cs in (
                dash.models.CampaignSettings.objects
                .filter(campaign_id__in=set([ca.ad_group.campaign_id for ca in content_ads]))
                .group_current_settings()
                .only('campaign_id', 'language')
            )
        }

        response = []
        for item in content_ads:
            video_asset = None
            video_asset_obj = item.video_asset
            if video_asset_obj:
                video_asset = {
                    'id': str(video_asset_obj.id),
                    'duration': video_asset_obj.duration,
                    'formats': video_asset_obj.formats,
                }
            content_ad = {
                'id': item.id,
                'ad_group_id': item.ad_group_id,
                'campaign_id': item.ad_group.campaign_id,
                'account_id': item.ad_group.campaign.account_id,
                'agency_id': item.ad_group.campaign.account.agency_id,
                'language': campaign_settings_map[item.ad_group.campaign_id].language,
                'title': item.title,
                'url': item.url,
                'redirect_id': item.redirect_id,
                'image_id': item.image_id,
                'image_width': item.image_width,
                'image_height': item.image_height,
                'image_hash': item.image_hash,
                'image_crop': item.image_crop,
                'description': item.description,
                'brand_name': item.brand_name,
                'display_url': item.display_url,
                'call_to_action': item.call_to_action,
                'tracker_urls': item.tracker_urls,
                'video_asset': video_asset,
                'label': item.label,
            }
            response.append(content_ad)

        return self.response_ok(response)


class ContentAdSourcesView(K1APIView):

    @db_for_reads.use_read_replica()
    def get(self, request):
        content_ad_ids = request.GET.get('content_ad_ids')
        ad_group_ids = request.GET.get('ad_group_ids')
        source_types = request.GET.get('source_types')
        slugs = request.GET.get('source_slugs')
        source_content_ad_ids = request.GET.get('source_content_ad_ids')
        content_ad_sources = (
            dash.models.ContentAdSource.objects
            .filter(source__deprecated=False)
            .select_related('content_ad', 'source', 'content_ad__ad_group__campaign__account')
            .values('id',
                    'content_ad_id',
                    'content_ad__ad_group_id',
                    'content_ad__ad_group__campaign_id',
                    'content_ad__ad_group__campaign__account_id',
                    'content_ad__ad_group__campaign__account__agency_id',
                    'source_id',
                    'source__content_ad_submission_policy',
                    'source__bidder_slug',
                    'source__tracking_slug',
                    'source_content_ad_id',
                    'submission_status',
                    'state')
        )
        if not content_ad_ids:  # exclude archived if not querying by id explicitly
            content_ad_sources.filter(content_ad__archived=False)
        if content_ad_ids:
            content_ad_sources = content_ad_sources.filter(content_ad_id__in=content_ad_ids.split(','))
        if ad_group_ids:
            content_ad_sources = content_ad_sources.filter(content_ad__ad_group_id__in=ad_group_ids.split(','))
        if source_types:
            content_ad_sources = content_ad_sources.filter(source__source_type__type__in=source_types.split(','))
        if slugs:
            content_ad_sources = content_ad_sources.filter(source__bidder_slug__in=slugs.split(','))
        if source_content_ad_ids:
            content_ad_sources = content_ad_sources.filter(source_content_ad_id__in=source_content_ad_ids.split(','))

        if request.GET.get('use_filters', 'false') == 'true':
            content_ad_sources = dash.features.submission_filters.filter_valid_content_ad_sources(content_ad_sources)
        response = []
        for content_ad_source in content_ad_sources:
            response.append({
                'id': content_ad_source['id'],
                'content_ad_id': content_ad_source['content_ad_id'],
                'ad_group_id': content_ad_source['content_ad__ad_group_id'],
                'source_slug': content_ad_source['source__bidder_slug'],
                'tracking_slug': content_ad_source['source__tracking_slug'],
                'source_content_ad_id': content_ad_source['source_content_ad_id'],
                'submission_status': content_ad_source['submission_status'],
                'state': content_ad_source['state'],
            })

        return self.response_ok(response)

    def put(self, request):
        content_ad_id = request.GET.get('content_ad_id')
        source_slug = request.GET.get('source_slug')
        data = json.loads(request.body)

        content_ad_source = dash.models.ContentAdSource.objects \
            .filter(content_ad_id=content_ad_id) \
            .filter(source__bidder_slug=source_slug)

        if not content_ad_source:
            logger.exception(
                'update_content_ad_status: content_ad_source does not exist. content ad id: %d, source slug: %s',
                content_ad_id,
                source_slug
            )
            raise Http404

        modified = False
        content_ad_source = content_ad_source[0]
        if 'submission_status' in data and content_ad_source.submission_status != data['submission_status']:
            content_ad_source.submission_status = data['submission_status']
            if content_ad_source.submission_status == constants.ContentAdSubmissionStatus.APPROVED:
                content_ad_source.submission_errors = None
            modified = True

        if 'submission_errors' in data and content_ad_source.submission_errors != data['submission_errors']:
            content_ad_source.submission_errors = data['submission_errors']
            modified = True

        if 'source_content_ad_id' in data and content_ad_source.source_content_ad_id != data['source_content_ad_id']:
            if content_ad_source.source_content_ad_id:
                return self.response_error("Cannot change existing source_content_ad_id", status=400)
            content_ad_source.source_content_ad_id = data['source_content_ad_id']
            modified = True

        if modified:
            content_ad_source.save()

        return self.response_ok(data)


class OutbrainMarketerIdView(K1APIView):

    def get(self, request):

        ad_group_id = request.GET.get('ad_group_id')
        try:
            ad_group = dash.models.AdGroup.objects.select_related('campaign__account').get(pk=ad_group_id)
        except dash.models.AdGroup.DoesNotExist:
            logger.exception('get_outbrain_marketer_id: ad group %s does not exist' % ad_group_id)
            raise Http404
        if ad_group.campaign.account.outbrain_marketer_id:
            return self.response_ok(ad_group.campaign.account.outbrain_marketer_id)

        try:
            unused_accounts = dash.models.OutbrainAccount.objects.\
                filter(used=False).order_by('created_dt')
            if len(unused_accounts) == 10 or len(unused_accounts) == 3:
                email_helper.send_outbrain_accounts_running_out_email(len(unused_accounts))
            outbrain_account = unused_accounts[0]
        except IndexError:
            raise Exception('No unused Outbrain accounts available.')

        outbrain_account.used = True
        outbrain_account.save()

        ad_group.campaign.account.outbrain_marketer_id = outbrain_account.marketer_id
        ad_group.campaign.account.save(request)

        return self.response_ok(ad_group.campaign.account.outbrain_marketer_id)


class OutbrainMarketerSyncView(K1APIView):

    def put(self, request):

        marketer_id = request.GET.get('marketer_id')
        marketer_name = request.GET.get('marketer_name')
        if not marketer_id:
            return self.response_error('Marketer id parameter is missing', status=400)
        try:
            ob_account = dash.models.OutbrainAccount.objects.get(marketer_id=marketer_id)
            if marketer_name and ob_account.marketer_name != marketer_name:
                ob_account.marketer_name = marketer_name
                ob_account.save()
            created = False
        except dash.models.OutbrainAccount.DoesNotExist:
            if not marketer_name:
                return self.response_error('Marketer name parameter is missing', status=400)
            ob_account = dash.models.OutbrainAccount.objects.create(
                marketer_id=marketer_id,
                marketer_name=marketer_name,
                used=False
            )
            created = True

        return self.response_ok({
            'created': created,
            'marketer_id': ob_account.marketer_id,
            'marketer_name': ob_account.marketer_name,
            'used': ob_account.used,
        })


class FacebookAccountsView(K1APIView):

    def get(self, request):
        ad_group_id = request.GET.get('ad_group_id')
        account_id = request.GET.get('account_id')
        if not ad_group_id and not account_id:
            facebook_accounts = dash.models.FacebookAccount.objects.filter(
                status=constants.FacebookPageRequestType.CONNECTED)

            result = []
            for facebook_account in facebook_accounts:
                account_dict = {
                    'account_id': facebook_account.account_id,
                    'ad_account_id': facebook_account.ad_account_id,
                    'page_id': facebook_account.page_id
                }
                result.append(account_dict)
            return self.response_ok(result)

        if not account_id:
            account_id = dash.models.Account.objects.get(campaign__adgroup__id=ad_group_id).id

        try:
            query_facebook_account = (
                dash.models.FacebookAccount.objects
                    .get(status=constants.FacebookPageRequestType.CONNECTED, account__id=account_id)
            )
            facebook_account = {
                'account_id': query_facebook_account.account_id,
                'ad_account_id': query_facebook_account.ad_account_id,
                'page_id': query_facebook_account.page_id
            }
        except dash.models.FacebookAccount.DoesNotExist:
            facebook_account = None
        return self.response_ok(facebook_account)

    def put(self, request):
        values = json.loads(request.body)
        account_id = values.get('account_id')
        if not account_id:
            return self.response_error('account id must be specified')
        try:
            facebook_account = dash.models.FacebookAccount.objects.get(account__id=account_id)
        except dash.models.FacebookAccount.DoesNotExist:
            return self.response_error(
                "No Facebook account exists for account_id: %s" % account_id, status=404)

        modified = False
        if values.get('ad_account_id'):
            facebook_account.ad_account_id = values['ad_account_id']
            modified = True

        if values.get('status'):
            facebook_account.status = values['status']
            modified = True

        if modified:
            facebook_account.save()
        return self.response_ok(values)


class GeolocationsView(K1APIView):

    @db_for_reads.use_read_replica()
    def get(self, request):
        keys = request.GET.get('keys')
        keys = keys.split(',') if keys else []
        geolocations = dash.features.geolocation.Geolocation.objects.filter(key__in=keys)
        response = geolocations.values('key', 'name', 'woeid', 'outbrain_id')
        return self.response_ok(list(response))


class PublisherBidModifiersView(K1APIView):

    def get(self, request):
        limit = int(request.GET.get('limit', 500))
        marker = request.GET.get('marker')
        ad_group_ids = request.GET.get('ad_group_ids')
        source_type = request.GET.get('source_type')

        qs = (
            core.publisher_bid_modifiers.PublisherBidModifier.objects.all()
            .select_related('source', 'source__source_type')
            .order_by('pk')
        )
        if ad_group_ids:
            ad_group_ids = ad_group_ids.split(',')
            qs = qs.filter(ad_group_id__in=ad_group_ids)
        if source_type:
            qs = qs.filter(source__source_type__type=source_type)
        if marker:
            qs = qs.filter(pk__gt=int(marker))
        qs = qs[:limit]

        return self.response_ok(
            [{
                'id': item.id,
                'ad_group_id': item.ad_group_id,
                'publisher': item.publisher,
                'source': item.source.bidder_slug,
                'modifier': item.modifier,
            } for item in qs]
        )
