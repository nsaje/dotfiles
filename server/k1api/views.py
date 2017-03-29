import json
import logging
import re
from collections import defaultdict
import datetime

from django.conf import settings
from django.db import transaction
from django.db.models import Q, F
from django.http import JsonResponse, Http404
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

import dash.constants
import dash.models
from dash import constants, publisher_helpers, publisher_group_helpers
from utils import redirector_helper, email_helper
from utils import url_helper, request_signer, converters
from redshiftapi import quickstats
import dash.geolocation


logger = logging.getLogger(__name__)

EVENT_RETARGET_ADGROUP = "redirect_adgroup"
EVENT_CUSTOM_AUDIENCE = "aud"


class K1APIView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        self._validate_signature(request)
        return super(K1APIView, self).dispatch(request, *args, **kwargs)

    @staticmethod
    def _validate_signature(request):
        try:
            request_signer.verify_wsgi_request(request, settings.K1_API_SIGN_KEY)
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
            for pixel in account.conversionpixel_set.all():
                if pixel.archived:
                    continue

                source_pixels = []
                for source_pixel in pixel.sourcetypepixel_set.all():
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
                     .prefetch_related('audiencerule_set'))
        for audience in audiences:
            rules = []
            for rule in audience.audiencerule_set.all():
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

    def get(self, request):
        all_current_settings = dash.models.CampaignSettings.objects.all().group_current_settings()
        ga_accounts = set()
        for current_settings in all_current_settings:
            if not (current_settings.enable_ga_tracking and
                    current_settings.ga_tracking_type == dash.constants.GATrackingType.API):
                continue
            ga_property_id = current_settings.ga_property_id
            ga_accounts.add((
                current_settings.campaign.account_id,
                self._extract_ga_account_id(ga_property_id),
                ga_property_id
            ))
        ga_accounts_dicts = [
            {'account_id': account_id, 'ga_account_id': ga_account_id, 'ga_web_property_id': ga_web_property_id}
            for account_id, ga_account_id, ga_web_property_id in ga_accounts
        ]

        return self.response_ok({'ga_accounts': list(ga_accounts_dicts)})

    @staticmethod
    def _extract_ga_account_id(ga_property_id):
        result = re.search(constants.GA_PROPERTY_ID_REGEX, ga_property_id)
        return result.group(1)


class R1MappingView(K1APIView):

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
        ).values('source_slug', 'publisher_group_id', 'include_subdomains', 'outbrain_publisher_id', 'publisher', 'account_id')))


class AdGroupsView(K1APIView):
    """
    Returns a list of non-archived ad groups together with their current settings.

    Filterable by ad_group_id, source_type and slug.
    """

    def get(self, request):
        ad_group_ids = request.GET.get('ad_group_ids')
        source_types = request.GET.get('source_types')
        slugs = request.GET.get('source_slugs')
        if ad_group_ids:
            ad_group_ids = ad_group_ids.split(',')
        if source_types:
            source_types = source_types.split(',')
        if slugs:
            slugs = slugs.split(',')

        ad_groups_settings, campaigns_settings_map, accounts_settings_map = \
            self._get_settings_maps(ad_group_ids, source_types, slugs)
        campaign_goal_types = self._get_campaign_goal_types(campaigns_settings_map.keys())

        ad_groups = []
        for ad_group_settings in ad_groups_settings:
            campaign_settings = campaigns_settings_map[ad_group_settings.ad_group.campaign_id]
            account_settings = accounts_settings_map[ad_group_settings.ad_group.campaign.account_id]

            blacklist = ad_group_settings.blacklist_publisher_groups
            whitelist = ad_group_settings.whitelist_publisher_groups

            ad_group = ad_group_settings.ad_group
            blacklist, whitelist = publisher_group_helpers.concat_publisher_group_targeting(
                ad_group, ad_group_settings,
                ad_group.campaign, campaign_settings,
                ad_group.campaign.account, account_settings,
                include_global=False  # global blacklist is handled separately by the bidder, no need to duplicate work
            )

            ad_group = {
                'id': ad_group.id,
                'name': ad_group.get_external_name(),
                'start_date': ad_group_settings.start_date,
                'end_date': ad_group_settings.end_date,
                'time_zone': settings.DEFAULT_TIME_ZONE,
                'brand_name': ad_group_settings.brand_name,
                'display_url': ad_group_settings.display_url,
                'tracking_codes': ad_group_settings.get_tracking_codes(),
                'target_devices': ad_group_settings.target_devices,
                'target_regions': ad_group_settings.target_regions,
                'exclusion_target_regions': ad_group_settings.exclusion_target_regions,
                'iab_category': campaign_settings.iab_category,
                'retargeting': self._get_retargeting(ad_group_settings),
                'demographic_targeting': ad_group_settings.bluekai_targeting,
                'interest_targeting': ad_group_settings.interest_targeting,
                'exclusion_interest_targeting': ad_group_settings.exclusion_interest_targeting,
                'campaign_id': ad_group.campaign.id,
                'account_id': ad_group.campaign.account.id,
                'agency_id': ad_group.campaign.account.agency_id,
                'goal_types': campaign_goal_types[ad_group.campaign.id],
                'dayparting': ad_group_settings.dayparting,
                'max_cpm': ad_group_settings.max_cpm,
                'b1_sources_group': {
                    'enabled': ad_group_settings.b1_sources_group_enabled,
                    'daily_budget': ad_group_settings.b1_sources_group_daily_budget,
                    'state': ad_group_settings.b1_sources_group_state,
                },
                'whitelist_publisher_groups': whitelist,
                'blacklist_publisher_groups': blacklist,
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
    def _get_campaign_goal_types(campaign_ids):
        '''
        returns a map campaign_id:[goal_type,...]
        the first element in the list is the type of the primary goal
        '''
        campaign_goals = {cid: [] for cid in campaign_ids}
        for goal in dash.models.CampaignGoal.objects.filter(campaign__in=campaign_ids):
            campaign_goals[goal.campaign_id].append((goal.primary, goal.type))
        for cid in campaign_goals.keys():
            campaign_goals[cid] = [tup[1] for tup in sorted(campaign_goals[cid], reverse=True)]
        return campaign_goals

    @staticmethod
    def _get_settings_maps(ad_group_ids, source_types, slugs):
        current_ad_groups_settings = dash.models.AdGroupSettings.objects.all().group_current_settings()

        if ad_group_ids:
            current_ad_groups_settings = current_ad_groups_settings.filter(ad_group_id__in=ad_group_ids)

        if source_types or slugs:
            ad_group_sources = dash.models.AdGroupSource.objects.all()
            if source_types:
                ad_group_sources = ad_group_sources.filter(source__source_type__type__in=source_types)
            if slugs:
                ad_group_sources = ad_group_sources.filter(source__bidder_slug__in=slugs)
            current_ad_groups_settings = current_ad_groups_settings.filter(
                ad_group_id__in=ad_group_sources.values('ad_group_id')
            )

        ad_groups_settings = (dash.models.AdGroupSettings.objects
                              .filter(pk__in=current_ad_groups_settings)
                              .filter(archived=False)
                              .select_related('ad_group', 'ad_group__campaign', 'ad_group__campaign__account'))

        campaigns_settings = (dash.models.CampaignSettings.objects
                              .filter(campaign_id__in=set([ag.ad_group.campaign_id for ag in ad_groups_settings]))
                              .group_current_settings()
                              .only('campaign_id', 'iab_category', 'whitelist_publisher_groups', 'blacklist_publisher_groups'))
        campaigns_settings_map = {cs.campaign_id: cs for cs in campaigns_settings}

        accounts_settings = (dash.models.AccountSettings.objects
                             .filter(account_id__in=set([ag.ad_group.campaign.account_id for ag in ad_groups_settings]))
                             .group_current_settings()
                             .only('account_id', 'whitelist_publisher_groups', 'blacklist_publisher_groups'))
        accounts_settings_map = {accs.account_id: accs for accs in accounts_settings}

        return ad_groups_settings, campaigns_settings_map, accounts_settings_map


class AdGroupStatsView(K1APIView):
    """
    Returns quickstats for an adgroup (used for decision making based on whether the ad group has spent already)
    """

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
        stats = quickstats.query_adgroup(ad_group.id, from_date, to_date, source.id)
        return self.response_ok({
            'total_cost': stats['total_cost'],
            'impressions': stats['impressions'],
            'clicks': stats['clicks'],
            'cpc': stats['cpc'],
        })


class AdGroupSourcesView(K1APIView):

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
        ad_groups = dash.models.AdGroup.objects.all().exclude_archived()
        if ad_group_ids:
            ad_groups = ad_groups.filter(id__in=ad_group_ids)

        ad_groups_settings_query = dash.models.AdGroupSettings.objects.filter(ad_group__in=ad_groups)
        ad_groups_settings = ad_groups_settings_query.group_current_settings()

        ad_group_settings_map = {ags.ad_group_id: ags for ags in ad_groups_settings}

        ag_source_settings_query = (dash.models.AdGroupSourceSettings.objects
                                    .filter(ad_group_source__ad_group__in=ad_group_settings_map.keys())
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
                                    .select_related('ad_group_source',
                                                    'ad_group_source__source',
                                                    'ad_group_source__source__source_type'))

        # build the list of objects
        ad_group_sources = []
        for ad_group_source_settings in ad_group_source_settings:
            ad_group_settings = ad_group_settings_map[ad_group_source_settings.ad_group_source.ad_group_id]
            if self._is_ad_group_source_enabled(ad_group_settings, ad_group_source_settings):
                source_state = constants.AdGroupSettingsState.ACTIVE
            else:
                source_state = constants.AdGroupSettingsState.INACTIVE
            # NOTE(nsaje): taking adgroupsource.blockers into account here is not necessary, since the
            # executor should know when it has a blocking action pending

            tracking_code = url_helper.combine_tracking_codes(
                ad_group_settings.get_tracking_codes(), ''
            )

            source = {
                'ad_group_id': ad_group_settings.ad_group_id,
                'slug': ad_group_source_settings.ad_group_source.source.bidder_slug,
                'source_campaign_key': ad_group_source_settings.ad_group_source.source_campaign_key,
                'tracking_code': tracking_code,
                'state': source_state,
                'cpc_cc': ad_group_source_settings.cpc_cc,
                'daily_budget_cc': ad_group_source_settings.daily_budget_cc,
            }
            ad_group_sources.append(source)

        return self.response_ok(ad_group_sources)

    def _is_ad_group_source_enabled(self, ad_group_settings, ad_group_source_settings):
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
        for key, val in data.items():
            if key == 'cpc_cc':
                new_settings.cpc_cc = converters.cc_to_decimal(val)
                settings_changed = True
            elif key == 'daily_budget_cc':
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
            new_settings.system_user = dash.constants.SystemUserType.K1_USER
            new_settings.save(None)
        return self.response_ok([])


class AdGroupSourceBlockersView(K1APIView):

    def put(self, request):
        """
        Add/remove a blocker of an ad group source.
        """
        ad_group_id = request.GET.get('ad_group_id')
        source_slug = request.GET.get('source_slug')
        ad_group_source = dash.models.AdGroupSource.objects.get(
            ad_group_id=ad_group_id, source__bidder_slug=source_slug)

        blockers_update = json.loads(request.body)
        for key, value in blockers_update.items():
            if not (isinstance(key, basestring) and (isinstance(value, basestring) or value is None)):
                return self.response_error("Bad input: blocker key should be string and value should be either string or None", status=400)
            if value:
                ad_group_source.blockers[key] = value
            if not value and key in ad_group_source.blockers:
                del ad_group_source.blockers[key]

        ad_group_source.save()
        return self.response_ok(ad_group_source.blockers)


class ContentAdsView(K1APIView):

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

        response = []
        for item in content_ads:
            content_ad = {
                'id': item.id,
                'ad_group_id': item.ad_group_id,
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
            }
            response.append(content_ad)

        return self.response_ok(response)


class ContentAdSourcesView(K1APIView):

    def get(self, request):
        content_ad_ids = request.GET.get('content_ad_ids')
        ad_group_ids = request.GET.get('ad_group_ids')
        source_types = request.GET.get('source_types')
        slugs = request.GET.get('source_slugs')
        source_content_ad_ids = request.GET.get('source_content_ad_ids')
        content_ad_sources = (
            dash.models.ContentAdSource.objects
            .filter(source__deprecated=False)
            .select_related('content_ad', 'source')
            .values('id',
                    'content_ad_id',
                    'content_ad__ad_group_id',
                    'source__bidder_slug',
                    'source__tracking_slug',
                    'source_content_ad_id',
                    'submission_status',
                    'state')
        )
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
            if len(unused_accounts) == 3:
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

    def get(self, request):
        keys = request.GET.get('keys')
        keys = keys.split(',') if keys else []
        geolocations = dash.geolocation.Geolocation.objects.filter(key__in=keys)
        response = geolocations.values('key', 'name', 'woeid', 'outbrain_id')
        return self.response_ok(list(response))
