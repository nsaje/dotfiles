import datetime
import json
import slugify
import StringIO
import unicodecsv

from django.db import transaction

import influx

from automation import autopilot_plus
from automation import campaign_stop

from dash import api
from dash import constants
from dash import forms
from dash import models
from dash import retargeting_helper
from dash import table
from dash.dashapi import data_helper
from dash.views import helpers
from dash.views import breakdown_helpers

from utils import api_common
from utils import exc
from utils import k1_helper


class BaseBulkActionView(api_common.BaseApiView):
    def create_rows(self, entities, archived=None, state=None):
        return {
            'rows': [self.create_row(entity.id, archived, state) for entity in entities]
        }

    def create_row(self, entity_id, archived=None, state=None, stats=None):
        row = {
            'breakdownId': str(entity_id),
        }
        if archived is not None:
            row['archived'] = archived
        if state is not None:
            row['stats'] = {
                'state': {'value': state},
                'status': {'value': state},
            }
        elif stats is not None:
            row['stats'] = stats
        return row


class AdGroupSourceState(BaseBulkActionView):
    @influx.timer('dash.api')
    def post(self, request, ad_group_id):
        last_change_dt = datetime.datetime.now()

        ad_group = helpers.get_ad_group(request.user, ad_group_id, select_related=True)

        data = json.loads(request.body)

        state = data.get('state')
        if state is None or state not in constants.AdGroupSourceSettingsState.get_all():
            raise exc.ValidationError()

        ad_group_sources = helpers.get_selected_adgroup_sources(
            models.AdGroupSource.objects.all().select_related('source'),
            data,
            ad_group_id=ad_group_id,
        )

        campaign_settings = ad_group.campaign.get_current_settings()
        ad_group_settings = ad_group.get_current_settings()

        self._check_can_set_state(campaign_settings, ad_group_settings, ad_group, ad_group_sources, state)

        with transaction.atomic():
            for ad_group_source in ad_group_sources:
                settings_writer = api.AdGroupSourceSettingsWriter(ad_group_source)
                settings_writer.set({'state': state}, request)

        if ad_group_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
            autopilot_plus.initialize_budget_autopilot_on_ad_group(ad_group, send_mail=False)

        k1_helper.update_ad_group(ad_group.pk, msg='AdGroupSourceState.post')

        editable_fields = self._get_editable_fields(ad_group, ad_group_settings, campaign_settings, ad_group_sources)
        response = {
            'rows': [
                self.create_row(ad_group_source.source_id, stats={
                    'status': {
                        'value': state,
                    },
                    'state': {
                        'value': state,
                        'isEditable': editable_fields[ad_group_source.id]['status_setting']['enabled'],
                        'editMessage': editable_fields[ad_group_source.id]['status_setting']['message'],
                    }
                }) for ad_group_source in ad_group_sources
            ]
        }

        self._apply_updates(request, response, last_change_dt, ad_group_id)

        return self.create_api_response(response)

    def _get_editable_fields(self, ad_group, ad_group_settings, campaign_settings, ad_group_sources):
        can_enable_source = campaign_stop.can_enable_media_sources(ad_group, ad_group.campaign, campaign_settings, ad_group_settings)
        allowed_sources = ad_group.campaign.account.allowed_sources.all().values_list('pk', flat=True)
        ad_group_source_settings = {
            agss.ad_group_source_id: agss
            for agss in models.AdGroupSourceSettings.objects.filter(ad_group_source__in=ad_group_sources).group_current_settings()
        }
        return {
            ad_group_source.id: helpers.get_editable_fields(
                ad_group,
                ad_group_source,
                ad_group_settings,
                ad_group_source_settings.get(ad_group_source.id),
                campaign_settings,
                allowed_sources,
                can_enable_source[ad_group_source.id],
            ) for ad_group_source in ad_group_sources
        }

    def _apply_updates(self, request, response, last_change_dt, ad_group_id):
        response_update = table.AdGroupSourcesTableUpdates().get(
            request.user, last_change_dt, [], ad_group_id_=ad_group_id)
        for row_id, row_update in response_update['rows'].iteritems():
            row = self._get_row(response, row_id)
            if 'stats' not in row:
                row['stats'] = {}
            row['stats'].update(self._convert_stats(row_update))
        if 'totals' in response_update:
            response['totals'] = self._convert_stats(response_update['totals'])

    def _convert_stats(self, stats):
        new_stats = {}
        for field, value in stats.iteritems():
            if field[:6] == 'status':
                continue
            new_stats[field] = {
                'value': value,
            }
        return new_stats

    def _get_row(self, response, row_id):
        row_id = str(row_id)
        for row in response['rows']:
            if row['breakdownId'] == row_id:
                return row

        new_row = {
            'breakdownId': row_id,
        }
        response['rows'].append(new_row)
        return new_row

    def _check_can_set_state(self, campaign_settings, ad_group_settings, ad_group, ad_group_sources, state):
        if campaign_settings.landing_mode:
            raise exc.ValidationError('Not allowed')
        if not campaign_stop.can_enable_all_media_sources(ad_group.campaign, campaign_settings, ad_group_sources, ad_group_settings):
            raise exc.ValidationError('Please add additional budget to your campaign to make changes.')

        if state == constants.AdGroupSourceSettingsState.ACTIVE:
            for ad_group_source in ad_group_sources:
                if not retargeting_helper.can_add_source_with_retargeting(ad_group_source.source, ad_group_settings):
                    raise exc.ValidationError(
                        'Cannot enable media source that does not support'
                        'retargeting on adgroup with retargeting enabled.'
                    )
                if not helpers.check_facebook_source(ad_group_source):
                    raise exc.ValidationError('Cannot enable Facebook media source that isn\'t connected to a Facebook page.')


class AdGroupContentAdArchive(BaseBulkActionView):

    @influx.timer('dash.api')
    def post(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.ForbiddenError(message="Not allowed")

        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        content_ads = helpers.get_selected_entities_post_request(
            models.ContentAd.objects,
            json.loads(request.body),
            ad_group_id=ad_group.id,
        )

        active_content_ads = content_ads.filter(state=constants.ContentAdSourceState.ACTIVE)
        if active_content_ads.exists():
            api.update_content_ads_state(active_content_ads, constants.ContentAdSourceState.INACTIVE, request)

        response = {
            'activeCount': active_content_ads.count()
        }

        # reload
        content_ads = content_ads.all()

        api.update_content_ads_archived_state(request, content_ads, ad_group, archived=True)
        k1_helper.update_content_ads(ad_group.pk, [ad.pk for ad in content_ads],
                                     msg='AdGroupContentAdArchive.post')

        response['archivedCount'] = content_ads.count()
        response.update(self.create_rows(content_ads, archived=True, state=constants.ContentAdSourceState.INACTIVE))

        return self.create_api_response(response)


class AdGroupContentAdRestore(BaseBulkActionView):

    @influx.timer('dash.api')
    def post(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.ForbiddenError(message="Not allowed")

        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        content_ads = helpers.get_selected_entities_post_request(
            models.ContentAd.objects,
            json.loads(request.body),
            include_archived=True,
            ad_group_id=ad_group.id,
        )

        api.update_content_ads_archived_state(request, content_ads, ad_group, archived=False)
        k1_helper.update_content_ads(ad_group.pk, [ad.pk for ad in content_ads],
                                     msg='AdGroupContentAdRestore.post')

        return self.create_api_response(
            self.create_rows(content_ads, archived=False, state=constants.ContentAdSourceState.INACTIVE)
        )


class AdGroupContentAdState(BaseBulkActionView):

    @influx.timer('dash.api')
    def post(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        data = json.loads(request.body)

        state = data.get('state')
        if state is None or state not in constants.ContentAdSourceState.get_all():
            raise exc.ValidationError()

        # TODO: maticz, 3.10.2016: This if is a hack so that users can start/pause content ads.
        if not data.get('selected_ids') and data.get('content_ad_ids_selected'):
            data['selected_ids'] = data.get('content_ad_ids_selected')
        content_ads = helpers.get_selected_entities_post_request(
            models.ContentAd.objects,
            data,
            ad_group_id=ad_group_id,
        )

        if content_ads.exists():
            api.update_content_ads_state(content_ads, state, request)
            api.add_content_ads_state_change_to_history_and_notify(ad_group, content_ads, state, request)
            k1_helper.update_content_ads(
                ad_group.pk, [ad.pk for ad in content_ads],
                msg='AdGroupContentAdState.post'
            )

        # refresh
        content_ads = content_ads.all()

        return self.create_api_response(self.create_rows(content_ads, state=state))


class AdGroupContentAdCSV(api_common.BaseApiView):

    @influx.timer('dash.api')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        select_all = request.GET.get('select_all', False)
        select_batch_id = request.GET.get('select_batch')
        include_archived = request.GET.get('archived') == 'true'

        content_ad_ids_selected = helpers.parse_get_request_content_ad_ids(request.GET, 'content_ad_ids_selected')
        content_ad_ids_not_selected = helpers.parse_get_request_content_ad_ids(
            request.GET, 'content_ad_ids_not_selected')

        content_ads = helpers.get_selected_entities(
            models.ContentAd.objects,
            select_all,
            content_ad_ids_selected,
            content_ad_ids_not_selected,
            include_archived=include_archived,
            select_batch_id=select_batch_id,
            ad_group_id=ad_group_id,
        )

        content_ad_dicts = []
        for content_ad in content_ads:
            content_ad_dict = {
                'url': content_ad.url,
                'title': content_ad.title,
                'image_url': content_ad.get_original_image_url(),
                'display_url': content_ad.display_url,
                'brand_name': content_ad.brand_name,
                'description': content_ad.description,
                'call_to_action': content_ad.call_to_action,
            }

            if content_ad.label:
                content_ad_dict['label'] = content_ad.label

            if content_ad.image_crop:
                content_ad_dict['image_crop'] = content_ad.image_crop

            if content_ad.crop_areas:
                content_ad_dict['crop_areas'] = content_ad.crop_areas

            if content_ad.tracker_urls:
                if len(content_ad.tracker_urls) > 0:
                    content_ad_dict['primary_tracker_url'] = content_ad.tracker_urls[0]
                if len(content_ad.tracker_urls) > 1:
                    content_ad_dict['secondary_tracker_url'] = content_ad.tracker_urls[1]

            # delete keys that are not to be exported
            for k in content_ad_dict.keys():
                if k not in forms.CSV_EXPORT_COLUMN_NAMES_DICT.keys():
                    del content_ad_dict[k]

            content_ad_dicts.append(content_ad_dict)

        filename = '{}_{}_{}_content_ads'.format(
            slugify.slugify(ad_group.campaign.account.name),
            slugify.slugify(ad_group.name),
            datetime.datetime.now().strftime('%Y-%m-%d')
        )
        content = self._create_content_ad_csv(content_ad_dicts)

        return self.create_csv_response(filename, content=content)

    def _create_content_ad_csv(self, content_ads):
        string = StringIO.StringIO()

        writer = unicodecsv.DictWriter(string, forms.CSV_EXPORT_COLUMN_NAMES_DICT.keys())

        # write the header manually as it is different than keys in the dict
        writer.writerow(forms.CSV_EXPORT_COLUMN_NAMES_DICT)

        for row in content_ads:
            writer.writerow(row)

        return string.getvalue()


class CampaignAdGroupArchive(BaseBulkActionView):
    @influx.timer('dash.api')
    def post(self, request, campaign_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.ForbiddenError(message="Not allowed")

        campaign = helpers.get_campaign(request.user, campaign_id)

        ad_groups = helpers.get_selected_entities_post_request(
            models.AdGroup.objects,
            json.loads(request.body),
            campaign_id=campaign.id,
        )

        active_ad_groups = ad_groups.filter_active()
        if active_ad_groups.exists():
            raise exc.ValidationError('Can not archive active ad groups')

        with transaction.atomic():
            for ad_group in ad_groups:
                ad_group.archive(request)

        return self.create_api_response(self.create_rows(ad_groups, archived=True))


class CampaignAdGroupRestore(BaseBulkActionView):
    @influx.timer('dash.api')
    def post(self, request, campaign_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.ForbiddenError(message="Not allowed")

        campaign = helpers.get_campaign(request.user, campaign_id)

        ad_groups = helpers.get_selected_entities_post_request(
            models.AdGroup.objects,
            json.loads(request.body),
            include_archived=True,
            campaign_id=campaign.id,
        )

        with transaction.atomic():
            for ad_group in ad_groups:
                ad_group.restore(request)

                for ad_group_source in ad_group.adgroupsource_set.all():
                    api.refresh_publisher_blacklist(ad_group_source, request)

        return self.create_api_response(self.create_rows(ad_groups, archived=False))


class CampaignAdGroupState(BaseBulkActionView):
    @influx.timer('dash.api')
    def post(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)

        data = json.loads(request.body)

        state = data.get('state')
        if state is None or state not in constants.ContentAdSourceState.get_all():
            raise exc.ValidationError()

        ad_groups = helpers.get_selected_entities_post_request(
            models.AdGroup.objects,
            data,
            campaign_id=campaign.id,
        )

        campaign_settings = campaign.get_current_settings()
        helpers.validate_ad_groups_state(ad_groups, campaign, campaign_settings, state)

        with transaction.atomic():
            for ad_group in ad_groups:
                changed = ad_group.set_state(request, state)
                if changed:
                    k1_helper.update_ad_group(ad_group.pk, msg='AdGroupSettingsState.post')

        can_enable_ad_group = campaign_stop.can_enable_ad_groups(campaign, campaign_settings)
        has_available_budget = data_helper.campaign_has_available_budget(campaign)
        editable_fields = {
            ad_group.id: breakdown_helpers.get_ad_group_editable_fields(
                {'state': state},
                can_enable_ad_group[ad_group.id],
                has_available_budget,
            ) for ad_group in ad_groups
        }

        return self.create_api_response({
            'rows': [
                self.create_row(ad_group.id, stats={
                    'status': {
                        'value': state,
                    },
                    'state': {
                        'value': state,
                        'isEditable': editable_fields[ad_group.id]['state']['enabled'],
                        'editMessage': editable_fields[ad_group.id]['state']['message'],
                    }
                }) for ad_group in ad_groups
            ]
        })


class AccountCampaignArchive(BaseBulkActionView):
    @influx.timer('dash.api')
    def post(self, request, account_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.ForbiddenError(message="Not allowed")

        account = helpers.get_account(request.user, account_id)

        campaigns = helpers.get_selected_entities_post_request(
            models.Campaign.objects,
            json.loads(request.body),
            account_id=account.id,
        )

        active_ad_groups = models.AdGroup.objects.filter(campaign__in=campaigns).filter_active()
        if active_ad_groups.exists():
            raise exc.ValidationError('Can not archive active campaigns')

        with transaction.atomic():
            for campaign in campaigns:
                for budget in campaign.budgets.all():
                    if budget.state() in (constants.BudgetLineItemState.ACTIVE,
                                          constants.BudgetLineItemState.PENDING):
                        raise exc.ValidationError('Can not archive campaigns with active budget')
                campaign.archive(request)

        return self.create_api_response(self.create_rows(campaigns, archived=True))


class AccountCampaignRestore(BaseBulkActionView):
    @influx.timer('dash.api')
    def post(self, request, account_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.ForbiddenError(message="Not allowed")

        account = helpers.get_campaign(request.user, account_id)

        campaigns = helpers.get_selected_entities_post_request(
            models.Campaign.objects,
            json.loads(request.body),
            include_archived=True,
            account_id=account.id,
        )

        with transaction.atomic():
            for campaign in campaigns:
                campaign.restore(request)

        return self.create_api_response(self.create_rows(campaigns, archived=False))


class AllAccountsAccountArchive(BaseBulkActionView):
    @influx.timer('dash.api')
    def post(self, request):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.ForbiddenError(message="Not allowed")

        accounts = helpers.get_selected_entities_post_request(
            models.Account.objects.all().filter_by_user(request.user),
            json.loads(request.body),
        )

        active_ad_groups = models.AdGroup.objects.filter(campaign__account__in=accounts).filter_active()
        if active_ad_groups.exists():
            raise exc.ValidationError('Can not archive active accounts')

        with transaction.atomic():
            for account in accounts:
                account.archive(request)

        return self.create_api_response(self.create_rows(accounts, archived=True))


class AllAccountsAccountRestore(BaseBulkActionView):
    @influx.timer('dash.api')
    def post(self, request):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.ForbiddenError(message="Not allowed")

        accounts = helpers.get_selected_entities_post_request(
            models.Account.objects.all().filter_by_user(request.user),
            json.loads(request.body),
            include_archived=True,
        )

        with transaction.atomic():
            for account in accounts:
                account.restore(request)

        return self.create_api_response(self.create_rows(accounts, archived=False))
