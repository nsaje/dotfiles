import json
import logging
from collections import defaultdict

from django.conf import settings
from django.db.models import F, Q
from django.http import JsonResponse, Http404
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

import dash.constants
import dash.models
from dash import constants, publisher_helpers
from utils import url_helper, request_signer, converters


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


class get_accounts(K1APIView):

    def get(self, request):
        account_id = request.GET.get('account_id')
        if account_id:
            accounts = (dash.models.Account.objects
                        .filter(id=account_id)
                        .prefetch_related('conversionpixel_set', 'conversionpixel_set__sourcetypepixel_set'))
        else:
            accounts = (dash.models.Account.objects
                        .all()
                        .exclude_archived()
                        .prefetch_related('conversionpixel_set', 'conversionpixel_set__sourcetypepixel_set'))

        account_dicts = []
        for account in accounts:
            pixels = []
            for pixel in account.conversionpixel_set.all():
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
                    'slug': pixel.slug,
                    'source_pixels': source_pixels,
                }
                pixels.append(pixel_dict)

            account_dict = {
                'id': account.id,
                'pixels': pixels,
                'outbrain_marketer_id': account.outbrain_marketer_id,
            }
            account_dicts.append(account_dict)
        response = {'accounts': account_dicts}

        bidder_slug = request.GET.get("bidder_slug")
        if bidder_slug:
            default_source_settings = dash.models.DefaultSourceSettings.objects.get(source__bidder_slug=bidder_slug)
            response['credentials'] = default_source_settings.credentials.credentials

        return self.response_ok(response)


class get_default_source_credentials(K1APIView):
    def get(self, request):
        bidder_slug = request.GET.get("bidder_slug")
        if not bidder_slug:
            return self.response_error("Must provide bidder slug.")

        default_source_settings = dash.models.DefaultSourceSettings.objects.get(source__bidder_slug=bidder_slug)
        return self.response_ok(default_source_settings.credentials.credentials)


class get_custom_audiences(K1APIView):

    def get(self, request):
        account_id = request.GET.get('account_id')
        if not account_id:
            return self.response_error('Account id must be specified.')

        audiences = dash.models.Audience.objects.filter(pixel__account__id=account_id).prefetch_related('rule_set')

        audiences_dicts = []
        for audience in audiences:
            rules = []
            for rule in audience.rule_set.all():
                rule_dict = {
                    'id': rule.id,
                    'type': rule.type,
                    'values': rule.value,
                }
                rules.append(rule_dict)

            audience_dict = {
                'id': audience.id,
                'pixel_id': audience.pixel.id,
                'ttl': audience.ttl,
                'rules': rules,
            }
            audiences_dicts.append(audience_dict)

        return self.response_ok(audiences_dicts)


class update_source_pixel(K1APIView):

    def put(self, request):
        data = json.loads(request.body)
        pixel_id = data['pixel_id']
        source_type = data['source_type']

        source_pixel, created = dash.models.SourceTypePixel.objects.get_or_create(
            pixel__id=pixel_id,
            source_type__type=source_type,
            defaults={
                'pixel': dash.models.ConversionPixel.objects.get(id=pixel_id),
                'source_type': dash.models.SourceType.objects.get(type=source_type),
            })

        source_pixel.url = data['url']
        source_pixel.source_pixel_id = data['source_pixel_id']
        source_pixel.save()

        return self.response_ok(data)


class get_source_credentials_for_reports_sync(K1APIView):

    def get(self, request):
        source_types = request.GET.getlist('source_type')

        source_credentials_list = (
            dash.models.SourceCredentials.objects
                .filter(sync_reports=True)
                .filter(source__source_type__type__in=source_types)
                .annotate(
                    source_type=F('source__source_type__type'),
                ).values(
                    'id',
                    'credentials',
                    'source_type',
                )
        )

        return self.response_ok({'source_credentials_list': list(source_credentials_list)})


class get_ga_accounts(K1APIView):

    def get(self, request):
        all_current_settings = dash.models.AdGroupSettings.objects.all().group_current_settings().prefetch_related(
            'ad_group')
        adgroup_ga_api_enabled = [current_settings.ad_group.id for current_settings in all_current_settings if
                                  current_settings.enable_ga_tracking and
                                  current_settings.ga_tracking_type == dash.constants.GATrackingType.API]

        ga_accounts = (dash.models.GAAnalyticsAccount.objects
                       .filter(account__campaign__adgroup__id__in=adgroup_ga_api_enabled)
                       .values('account_id', 'ga_account_id', 'ga_web_property_id')
                       .distinct()
                       .order_by('account_id', 'ga_account_id'))
        return self.response_ok({'ga_accounts': list(ga_accounts)})


class get_sources_by_tracking_slug(K1APIView):

    def get(self, request):
        data = {}

        sources = dash.models.Source.objects.all()
        for source in sources:
            data[source.tracking_slug] = {
                'id': source.id,
            }

        return self.response_ok(data)


class get_accounts_slugs_ad_groups(K1APIView):

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


class get_publishers_blacklist_outbrain(K1APIView):

    def get(self, request):
        marketer_id = request.GET.get('marketer_id')
        blacklisted_publishers = (
            dash.models.PublisherBlacklist.objects
                .filter(account__outbrain_marketer_id=marketer_id)
                .filter(source__source_type__type='outbrain')
                .values('name', 'external_id')
        )
        return self.response_ok({'blacklist': list(blacklisted_publishers)})


class get_publishers_blacklist(K1APIView):

    def get(self, request):
        ad_group_id = request.GET.get('ad_group_id')
        if ad_group_id:
            ad_group = dash.models.AdGroup.objects.get(id=ad_group_id)
            blacklist_filter = (Q(ad_group=ad_group) | Q(campaign=ad_group.campaign) |
                                Q(account=ad_group.campaign.account))
            blacklisted = (dash.models.PublisherBlacklist.objects
                           .filter(blacklist_filter)
                           .filter(Q(source__isnull=True) | Q(source__source_type__type='b1'))
                           .select_related('source', 'ad_group'))
        else:
            running_ad_groups = dash.models.AdGroup.objects.all().filter_running().select_related('campaign',
                                                                                                  'campaign__account')
            running_campaigns = set([ag.campaign for ag in running_ad_groups])
            running_accounts = set([c.account for c in running_campaigns])

            blacklist_filter = (Q(ad_group__isnull=True, campaign__isnull=True, account__isnull=True) |
                                Q(ad_group__in=running_ad_groups) |
                                Q(campaign__in=running_campaigns) |
                                Q(account__in=running_accounts))
            blacklisted = (dash.models.PublisherBlacklist.objects
                           .filter(blacklist_filter)
                           .filter(Q(source__isnull=True) | Q(source__source_type__type='b1'))
                           .select_related('source', 'ad_group', 'campaign', 'account', 'account')
                           .prefetch_related('campaign__adgroup_set',
                                             'account__campaign_set',
                                             'account__campaign_set__adgroup_set'))

        blacklist = {}
        for item in blacklisted:
            exchange = None
            if item.source is not None:
                exchange = publisher_helpers.publisher_exchange(item.source)

            # for single ad group ad_group_id is always the one queried
            if ad_group_id:
                entry = {
                    'ad_group_id': ad_group.id,
                    'domain': item.name,
                    'exchange': exchange,
                    'status': item.status,
                    'external_id': item.external_id,
                }
                blacklist[hash(tuple(entry.values()))] = entry
            # for all ad groups generate all ad_group_ids
            else:
                self._process_item(blacklist, item, exchange, running_ad_groups)

        return self.response_ok({'blacklist': list(blacklist.values())})

    @classmethod
    def _process_item(cls, blacklist, item, exchange, running_ad_groups):
        # if ad_group then use this ad_group_id
        if item.ad_group:
            entry = {
                'ad_group_id': item.ad_group_id,
                'domain': item.name,
                'exchange': exchange,
                'status': item.status,
                'external_id': item.external_id,
            }
            blacklist[hash(tuple(entry.values()))] = entry
        # if campaign then generate all running ad groups is this campaign
        elif item.campaign:
            cls._process_campaign(blacklist, item, item.campaign, exchange, running_ad_groups)
        # if account then generate all running ad groups in this account
        elif item.account:
            for campaign in item.account.campaign_set.all():
                cls._process_campaign(blacklist, item, campaign, exchange, running_ad_groups)
        # global blacklist
        else:
            entry = {
                'ad_group_id': None,
                'domain': item.name,
                'exchange': exchange,
                'status': item.status,
                'external_id': item.external_id,
            }
            blacklist[hash(tuple(entry.values()))] = entry

    @staticmethod
    def _process_campaign(blacklist, item, campaign, exchange, running_ad_groups):
        for ad_group in campaign.adgroup_set.all():
            if ad_group in running_ad_groups:
                entry = {
                    'ad_group_id': ad_group.id,
                    'domain': item.name,
                    'exchange': exchange,
                    'status': item.status,
                    'external_id': item.external_id,
                }
                blacklist[hash(tuple(entry.values()))] = entry


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

        ad_groups_settings, campaigns_settings_map = \
            self._get_ad_groups_and_campaigns_settings(ad_group_ids, source_types, slugs)
        campaign_goal_types = self._get_campaign_goal_types(campaigns_settings_map.keys())

        ad_groups = []
        for ad_group_settings in ad_groups_settings:
            ad_group = {
                'id': ad_group_settings.ad_group.id,
                'name': ad_group_settings.ad_group.get_external_name(),
                'start_date': ad_group_settings.start_date,
                'end_date': ad_group_settings.end_date,
                'time_zone': settings.DEFAULT_TIME_ZONE,
                'brand_name': ad_group_settings.brand_name,
                'display_url': ad_group_settings.display_url,
                'tracking_codes': ad_group_settings.get_tracking_codes(),
                'target_devices': ad_group_settings.target_devices,
                'target_regions': ad_group_settings.target_regions,
                'iab_category': campaigns_settings_map[ad_group_settings.ad_group.campaign.id].iab_category,
                'retargeting': self._get_retargeting(ad_group_settings),
                'campaign_id': ad_group_settings.ad_group.campaign.id,
                'account_id': ad_group_settings.ad_group.campaign.account.id,
                'agency_id': None,
                'goal_types': campaign_goal_types[ad_group_settings.ad_group.campaign.id],
            }

            if ad_group_settings.ad_group.campaign.account.agency:
                ad_group['agency_id'] = ad_group_settings.ad_group.campaign.account.agency.id

            ad_groups.append(ad_group)

        return self.response_ok(ad_groups)

    @staticmethod
    def _get_retargeting(ad_group_settings):
        retargeting = []

        for retargeting_ad_group_id in ad_group_settings.retargeting_ad_groups:
            retargeting.append(
                {'event_type': EVENT_RETARGET_ADGROUP, 'event_id': str(retargeting_ad_group_id), 'exclusion': False})

        for audience in ad_group_settings.audience_set.all():
            retargeting.append({'event_type': EVENT_CUSTOM_AUDIENCE, 'event_id': str(audience.id), 'exclusion': False})

        return retargeting

    @staticmethod
    def _get_campaign_goal_types(campaign_ids):
        '''
        returns a map campaign_id:[goal_type,...]
        the first element in the list is the type of the primary goal
        '''
        campaign_goals = {cid: [] for cid in campaign_ids}
        for goal in dash.models.CampaignGoal.objects.filter(campaign__in=campaign_ids):
            campaign_goals[goal.campaign.id].append((goal.primary, goal.type))
        for cid in campaign_goals.keys():
            campaign_goals[cid] = [tup[1] for tup in sorted(campaign_goals[cid], reverse=True)]
        return campaign_goals

    @staticmethod
    def _get_ad_groups_and_campaigns_settings(ad_group_ids, source_types, slugs):
        ad_groups = dash.models.AdGroup.objects.all().exclude_archived()

        if ad_group_ids:
            ad_groups = ad_groups.filter(id__in=ad_group_ids)

        if source_types or slugs:
            ad_group_sources = dash.models.AdGroupSource.objects.filter(ad_group__in=ad_groups)
            if source_types:
                ad_group_sources = ad_group_sources.filter(source__source_type__type__in=source_types)
            if slugs:
                ad_group_sources = ad_group_sources.filter(source__bidder_slug__in=slugs)
            ad_groups = ad_groups.filter(id__in=ad_group_sources.values('ad_group_id'))

        ad_groups_settings = (dash.models.AdGroupSettings.objects
                              .filter(ad_group__in=ad_groups)
                              .group_current_settings()
                              .select_related('ad_group', 'ad_group__campaign', 'ad_group__campaign__account')
                              .prefetch_related('audience_set'))

        campaigns_settings = (dash.models.CampaignSettings.objects
                              .filter(campaign__adgroup__in=ad_groups)
                              .group_current_settings()
                              .select_related('campaign'))
        campaigns_settings_map = {cs.campaign.id: cs for cs in campaigns_settings}

        return ad_groups_settings, campaigns_settings_map


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
        ad_groups_settings_query = dash.models.AdGroupSettings.objects.filter(archived=False)
        if ad_group_ids:
            ad_groups_settings_query = ad_groups_settings_query.filter(ad_group__id__in=ad_group_ids)

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
                                                    'ad_group_source__source'))

        # build the list of objects
        ad_group_sources = []
        for ad_group_source_settings in ad_group_source_settings:
            ad_group_settings = ad_group_settings_map[ad_group_source_settings.ad_group_source.ad_group_id]
            if (ad_group_settings.state == constants.AdGroupSettingsState.ACTIVE and
                    ad_group_source_settings.state == constants.AdGroupSourceSettingsState.ACTIVE):
                source_state = constants.AdGroupSettingsState.ACTIVE
            else:
                source_state = constants.AdGroupSettingsState.INACTIVE

            tracking_code = url_helper.combine_tracking_codes(
                ad_group_settings.get_tracking_codes(),
                (ad_group_source_settings.ad_group_source.get_tracking_ids()
                    if ad_group_settings.enable_ga_tracking else '')
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
                ad_group_source.source_campaign_key = val
                ad_group_source.save()
            else:
                return self.response_error("Invalid setting!", status=400)

        if settings_changed:
            new_settings.system_user = dash.constants.SystemUserType.K1_USER
            new_settings.save(None)
        return self.response_ok([])


class ContentAdsView(K1APIView):

    def get(self, request):
        content_ad_ids = request.GET.get('content_ad_ids')
        ad_group_ids = request.GET.get('ad_group_ids')
        content_ads = dash.models.ContentAd.objects.all()
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
            content_ad_source.source_content_ad_id = data['source_content_ad_id']
            modified = True

        if modified:
            content_ad_source.save()

        return self.response_ok(data)


class get_outbrain_marketer_id(K1APIView):

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
            outbrain_account = dash.models.OutbrainAccount.objects.\
                filter(used=False).order_by('created_dt')[0]
        except IndexError:
            raise Exception('No unused Outbrain accounts available.')

        outbrain_account.used = True
        outbrain_account.save()

        ad_group.campaign.account.outbrain_marketer_id = outbrain_account.marketer_id
        ad_group.campaign.account.save(request)

        return self.response_ok(ad_group.campaign.account.outbrain_marketer_id)


class get_facebook_accounts(K1APIView):

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


class update_facebook_account(K1APIView):

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
