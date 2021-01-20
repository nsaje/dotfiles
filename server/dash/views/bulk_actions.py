import datetime
import decimal
import json

import slugify
from django.db import transaction

import core.features.multicurrency
import core.models.content_ad_candidate.exceptions
import core.models.settings.ad_group_source_settings.exceptions
import dash.features.contentupload
import zemauth.access
from automation import autopilot
from automation import autopilot_legacy
from dash import api
from dash import constants
from dash import forms
from dash import legacy
from dash import models
from dash.common.views_base import DASHAPIBaseView
from dash.dashapi import data_helper
from dash.features import contentupload
from dash.views import breakdown_helpers
from dash.views import helpers
from utils import csv_utils
from utils import exc
from utils import k1_helper
from utils import metrics_compat
from zemauth.features.entity_permission import Permission


class BaseBulkActionView(DASHAPIBaseView):
    def create_rows(self, entities, archived=None, state=None):
        return {"rows": [self.create_row(entity.id, archived, state) for entity in entities]}

    def create_row(self, entity_id, archived=None, state=None, stats=None):
        row = {"breakdownId": str(entity_id)}
        if archived is not None:
            row["archived"] = archived
        if state is not None:
            row["stats"] = {"state": {"value": state}, "status": {"value": state}}
        elif stats is not None:
            row["stats"] = stats
        return row


class AdGroupSourceState(BaseBulkActionView):
    @metrics_compat.timer("dash.api")
    def post(self, request, ad_group_id):
        last_change_dt = datetime.datetime.now()

        ad_group = zemauth.access.get_ad_group(request.user, Permission.WRITE, ad_group_id)

        data = json.loads(request.body)

        state = data.get("state")
        if state is None or state not in constants.AdGroupSourceSettingsState.get_all():
            raise exc.ValidationError()

        ad_group_sources = helpers.get_selected_adgroup_sources(
            models.AdGroupSource.objects.all()
            .select_related("source")
            .filter(source__deprecated=False, source__maintenance=False),
            data,
            ad_group_id=ad_group_id,
        )

        campaign_settings = ad_group.campaign.get_current_settings()
        ad_group_settings = ad_group.get_current_settings()

        self._check_can_set_state(campaign_settings, ad_group_settings, ad_group, ad_group_sources, state)

        with transaction.atomic():
            for ad_group_source in ad_group_sources:
                self._update_ad_group_source(
                    request, ad_group_source, state=state, k1_sync=False, skip_automation=True, skip_validation=False
                )

        # TODO: RTAP: LEGACY
        if not ad_group.campaign.account.agency_uses_realtime_autopilot():
            if (
                ad_group.settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
                or ad_group.campaign.settings.autopilot
            ):
                autopilot_legacy.recalculate_budgets_ad_group(ad_group)
        else:
            if ad_group.campaign.settings.autopilot:
                autopilot.recalculate_ad_group_budgets(ad_group.campaign)

        k1_helper.update_ad_group(ad_group, msg="AdGroupSourceState.post")

        editable_fields = self._get_editable_fields(
            request.user, ad_group, ad_group_settings, campaign_settings, ad_group_sources
        )
        response = {
            "rows": [
                self.create_row(
                    ad_group_source.source_id,
                    stats={
                        "status": {"value": state},
                        "state": {
                            "value": state,
                            "isEditable": editable_fields[ad_group_source.id]["status_setting"]["enabled"],
                            "editMessage": editable_fields[ad_group_source.id]["status_setting"]["message"],
                        },
                    },
                )
                for ad_group_source in ad_group_sources
            ]
        }

        self._apply_updates(request, response, last_change_dt, ad_group_id)

        return self.create_api_response(response)

    def _update_ad_group_source(self, request, ad_group_source, **data):
        try:
            return ad_group_source.settings.update(request, **data)

        except core.models.settings.ad_group_source_settings.exceptions.MinimalDailyBudgetTooLow as err:
            raise exc.ValidationError(
                "{}: {}".format(
                    ad_group_source.source.name,
                    "Please provide daily spend cap of at least {}.".format(
                        core.features.multicurrency.format_value_in_currency(
                            err.data.get("value"), 0, decimal.ROUND_CEILING, ad_group_source.settings.get_currency()
                        )
                    ),
                )
            )

        except core.models.settings.ad_group_source_settings.exceptions.MaximalDailyBudgetTooHigh as err:
            raise exc.ValidationError(
                "{}: {}".format(
                    ad_group_source.source.name,
                    "Maximum allowed daily spend cap is {}."
                    "If you want use a higher daily spend cap, please contact support.".format(
                        core.features.multicurrency.format_value_in_currency(
                            err.data.get("value"), 0, decimal.ROUND_FLOOR, ad_group_source.settings.get_currency()
                        )
                    ),
                )
            )

        except core.models.settings.ad_group_source_settings.exceptions.MinimalCPCTooLow as err:
            raise exc.ValidationError(
                "{}: {}".format(
                    ad_group_source.source.name,
                    "Minimum CPC on {} is {}.".format(
                        err.data.get("source_name"),
                        core.features.multicurrency.format_value_in_currency(
                            err.data.get("value"), 2, decimal.ROUND_CEILING, ad_group_source.settings.get_currency()
                        ),
                    ),
                )
            )

        except core.models.settings.ad_group_source_settings.exceptions.MaximalCPCTooHigh as err:
            raise exc.ValidationError(
                "{}: {}".format(
                    ad_group_source.source.name,
                    "Maximum CPC on {} is {}.".format(
                        err.data.get("source_name"),
                        core.features.multicurrency.format_value_in_currency(
                            err.data.get("value"), 2, decimal.ROUND_FLOOR, ad_group_source.settings.get_currency()
                        ),
                    ),
                )
            )

        except core.models.settings.ad_group_source_settings.exceptions.MinimalCPMTooLow as err:
            raise exc.ValidationError(
                "{}: {}".format(
                    ad_group_source.source.name,
                    "Minimum CPM on {} is {}.".format(
                        err.data.get("source_name"),
                        core.features.multicurrency.format_value_in_currency(
                            err.data.get("value"), 2, decimal.ROUND_CEILING, ad_group_source.settings.get_currency()
                        ),
                    ),
                )
            )

        except core.models.settings.ad_group_source_settings.exceptions.MaximalCPMTooHigh as err:
            raise exc.ValidationError(
                "{}: {}".format(
                    ad_group_source.source.name,
                    "Maximum CPM on {} is {}.".format(
                        err.data.get("source_name"),
                        core.features.multicurrency.format_value_in_currency(
                            err.data.get("value"), 2, decimal.ROUND_FLOOR, ad_group_source.settings.get_currency()
                        ),
                    ),
                )
            )

        except (
            core.models.settings.ad_group_source_settings.exceptions.CannotSetCPC,
            core.models.settings.ad_group_source_settings.exceptions.CannotSetCPM,
            core.models.settings.ad_group_source_settings.exceptions.CPCInvalid,
            core.models.settings.ad_group_source_settings.exceptions.BudgetUpdateWhileSourcesGroupEnabled,
            core.models.settings.ad_group_source_settings.exceptions.MediaSourceNotConnectedToFacebook,
            core.models.settings.ad_group_source_settings.exceptions.AutopilotDailySpendCapTooLow,
        ) as err:
            raise exc.ValidationError("{}: {}".format(ad_group_source.source.name, str(err)))

    def _get_editable_fields(self, user, ad_group, ad_group_settings, campaign_settings, ad_group_sources):
        allowed_sources = ad_group.campaign.account.allowed_sources.all().values_list("pk", flat=True)
        ad_group_source_settings = {
            agss.ad_group_source_id: agss
            for agss in models.AdGroupSourceSettings.objects.filter(
                ad_group_source__in=ad_group_sources
            ).group_current_settings()
        }
        return {
            ad_group_source.id: helpers.get_editable_fields(
                user,
                ad_group,
                ad_group_source,
                ad_group_settings,
                ad_group_source_settings.get(ad_group_source.id),
                campaign_settings,
                allowed_sources,
            )
            for ad_group_source in ad_group_sources
        }

    def _apply_updates(self, request, response, last_change_dt, ad_group_id):
        response_update = legacy.get_updated_ad_group_sources_changes(
            request.user, last_change_dt, [], ad_group_id_=ad_group_id
        )
        if "rows" in response_update:
            for row_id, row_update in response_update["rows"].items():
                row = self._get_row(response, row_id)
                if "stats" not in row:
                    row["stats"] = {}
                row["stats"].update(self._convert_stats(row_update))
        if "totals" in response_update:
            response["totals"] = self._convert_stats(response_update["totals"])

    def _convert_stats(self, stats):
        new_stats = {}
        for field, value in stats.items():
            if field[:6] == "status":
                continue
            new_stats[field] = {"value": value}
        return new_stats

    def _get_row(self, response, row_id):
        row_id = str(row_id)
        for row in response["rows"]:
            if row["breakdownId"] == row_id:
                return row

        new_row = {"breakdownId": row_id}
        response["rows"].append(new_row)
        return new_row

    def _check_can_set_state(self, campaign_settings, ad_group_settings, ad_group, ad_group_sources, state):
        if state == constants.AdGroupSourceSettingsState.ACTIVE:
            # TODO: RTAP: LEGACY
            enabling_autopilot_sources_allowed = ad_group.campaign.account.agency_uses_realtime_autopilot() or helpers.enabling_autopilot_sources_allowed(
                ad_group, ad_group_sources
            )
            if not enabling_autopilot_sources_allowed:
                raise exc.ValidationError("Please increase Autopilot Daily Spend Cap to enable these sources.")


class AdGroupContentAdEdit(BaseBulkActionView):
    @metrics_compat.timer("dash.api")
    def post(self, request, ad_group_id):
        ad_group = zemauth.access.get_ad_group(request.user, Permission.WRITE, ad_group_id)
        content_ads = helpers.get_selected_entities_post_request(
            models.ContentAd.objects, json.loads(request.body), ad_group_id=ad_group.id
        )

        try:
            batch, candidates = contentupload.upload.insert_edit_candidates(request.user, content_ads, ad_group)

        except core.models.content_ad_candidate.exceptions.AdGroupIsArchived as err:
            raise exc.ValidationError(str(err))

        return self.create_api_response(
            {"batch_id": batch.id, "candidates": contentupload.upload.get_candidates_with_errors(request, candidates)}
        )


class AdGroupContentAdArchive(BaseBulkActionView):
    @metrics_compat.timer("dash.api")
    def post(self, request, ad_group_id):
        ad_group = zemauth.access.get_ad_group(request.user, Permission.WRITE, ad_group_id)

        content_ads = helpers.get_selected_entities_post_request(
            models.ContentAd.objects, json.loads(request.body), ad_group_id=ad_group.id
        )

        active_content_ads = content_ads.filter(state=constants.ContentAdSourceState.ACTIVE)
        if active_content_ads.exists():
            api.update_content_ads_state(active_content_ads, constants.ContentAdSourceState.INACTIVE, request)

        response = {"activeCount": active_content_ads.count()}

        # reload
        content_ads = content_ads.all()

        api.update_content_ads_archived_state(request, content_ads, ad_group, archived=True)
        k1_helper.update_content_ads(list(content_ads), msg="AdGroupContentAdArchive.post")

        response["archivedCount"] = content_ads.count()
        response.update(self.create_rows(content_ads, archived=True, state=constants.ContentAdSourceState.INACTIVE))

        return self.create_api_response(response)


class AdGroupContentAdRestore(BaseBulkActionView):
    @metrics_compat.timer("dash.api")
    def post(self, request, ad_group_id):
        ad_group = zemauth.access.get_ad_group(request.user, Permission.WRITE, ad_group_id)

        content_ads = helpers.get_selected_entities_post_request(
            models.ContentAd.objects, json.loads(request.body), include_archived=True, ad_group_id=ad_group.id
        )

        api.update_content_ads_archived_state(request, content_ads, ad_group, archived=False)
        k1_helper.update_content_ads(list(content_ads), msg="AdGroupContentAdRestore.post")

        return self.create_api_response(
            self.create_rows(content_ads, archived=False, state=constants.ContentAdSourceState.INACTIVE)
        )


class AdGroupContentAdState(BaseBulkActionView):
    @metrics_compat.timer("dash.api")
    def post(self, request, ad_group_id):
        ad_group = zemauth.access.get_ad_group(request.user, Permission.WRITE, ad_group_id)

        data = json.loads(request.body)

        state = data.get("state")
        if state is None or state not in constants.ContentAdSourceState.get_all():
            raise exc.ValidationError()

        # TODO: maticz, 3.10.2016: This if is a hack so that users can start/pause content ads.
        if not data.get("selected_ids") and data.get("content_ad_ids_selected"):
            data["selected_ids"] = data.get("content_ad_ids_selected")
        content_ads = helpers.get_selected_entities_post_request(
            models.ContentAd.objects, data, ad_group_id=ad_group_id
        )

        if content_ads.exists():
            api.update_content_ads_state(content_ads, state, request)
            api.add_content_ads_state_change_to_history_and_notify(ad_group, content_ads, state, request)
            k1_helper.update_content_ads(list(content_ads), msg="AdGroupContentAdState.post")

        # refresh
        content_ads = content_ads.all()

        return self.create_api_response(self.create_rows(content_ads, state=state))


class AdGroupContentAdCSV(DASHAPIBaseView):
    @metrics_compat.timer("dash.api")
    def get(self, request, ad_group_id):
        ad_group = zemauth.access.get_ad_group(request.user, Permission.READ, ad_group_id)

        select_all = request.GET.get("select_all", False)
        select_batch_id = request.GET.get("select_batch")
        include_archived = request.GET.get("archived") == "true"

        content_ad_ids_selected = helpers.parse_get_request_content_ad_ids(request.GET, "content_ad_ids_selected")
        content_ad_ids_not_selected = helpers.parse_get_request_content_ad_ids(
            request.GET, "content_ad_ids_not_selected"
        )

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
                "url": content_ad.url,
                "title": content_ad.title,
                "image_url": content_ad.get_base_image_url(),
                "display_url": content_ad.display_url,
                "brand_name": content_ad.brand_name,
                "description": content_ad.description,
                "call_to_action": content_ad.call_to_action,
            }

            if content_ad.label:
                content_ad_dict["label"] = content_ad.label

            if content_ad.image_crop:
                content_ad_dict["image_crop"] = content_ad.image_crop

            if content_ad.crop_areas:
                content_ad_dict["crop_areas"] = content_ad.crop_areas

            if ad_group.campaign.type != constants.CampaignType.DISPLAY:
                content_ad_dict["icon_url"] = content_ad.get_base_icon_url()

            if content_ad.tracker_urls:
                if len(content_ad.tracker_urls) > 0:
                    content_ad_dict["primary_tracker_url"] = content_ad.tracker_urls[0]
                if len(content_ad.tracker_urls) > 1:
                    content_ad_dict["secondary_tracker_url"] = content_ad.tracker_urls[1]

            if content_ad.trackers:
                content_ad_dict.update(dash.features.contentupload.map_trackers_to_csv(content_ad.trackers))

            if ad_group.campaign.type == constants.CampaignType.DISPLAY:
                content_ad_dict["ad_tag"] = content_ad.ad_tag
                if content_ad.image_width and content_ad.image_height:
                    content_ad_dict["creative_size"] = "x".join(
                        (str(content_ad.image_width), str(content_ad.image_height))
                    )

            # delete keys that are not to be exported
            for k in list(content_ad_dict.keys()):
                if k not in list(forms.CSV_EXPORT_COLUMN_NAMES_DICT.keys()):
                    del content_ad_dict[k]

            content_ad_dicts.append(content_ad_dict)

        filename = "{}_{}_{}_content_ads".format(
            slugify.slugify(ad_group.campaign.account.name),
            slugify.slugify(ad_group.name),
            datetime.datetime.now().strftime("%Y-%m-%d"),
        )

        fields = forms.CSV_EXPORT_COLUMN_NAMES_DICT.copy()
        fields = self._remove_ad_type_specific_fields(ad_group, fields)
        fields = self._remove_permissioned_fields(request, fields)

        content = csv_utils.dictlist_to_csv(
            list(fields.values()), self._map_to_csv_column_names(content_ad_dicts, fields)
        )

        return self.create_csv_response(filename, content=content)

    def _remove_ad_type_specific_fields(self, ad_group, fields):
        if ad_group.campaign.type != constants.CampaignType.DISPLAY:
            for field in forms.DISPLAY_SPECIFIC_FIELDS:
                fields.pop(field, None)
        else:
            for field in forms.NATIVE_SPECIFIC_FIELDS:
                fields.pop(field, None)
        return fields

    def _remove_permissioned_fields(self, request, fields):
        for field, permissions in forms.FIELD_PERMISSION_MAPPING.items():
            if not all(request.user.has_perm(p) for p in permissions):
                fields.pop(field, None)
        return fields

    def _map_to_csv_column_names(self, content_ads, fields):
        return [{fields[key]: content_ad.get(key) for key in fields.keys()} for content_ad in content_ads]


class CampaignAdGroupArchive(BaseBulkActionView):
    @metrics_compat.timer("dash.api")
    def post(self, request, campaign_id):
        campaign = zemauth.access.get_campaign(request.user, Permission.WRITE, campaign_id)

        ad_groups = helpers.get_selected_entities_post_request(
            models.AdGroup.objects, json.loads(request.body), campaign_id=campaign.id
        )

        with transaction.atomic():
            for ad_group in ad_groups:
                ad_group.archive(request)

        return self.create_api_response(self.create_rows(ad_groups, archived=True))


class CampaignAdGroupRestore(BaseBulkActionView):
    @metrics_compat.timer("dash.api")
    def post(self, request, campaign_id):
        campaign = zemauth.access.get_campaign(request.user, Permission.WRITE, campaign_id)

        ad_groups = helpers.get_selected_entities_post_request(
            models.AdGroup.objects, json.loads(request.body), include_archived=True, campaign_id=campaign.id
        )

        with transaction.atomic():
            for ad_group in ad_groups:
                ad_group.restore(request)

        return self.create_api_response(self.create_rows(ad_groups, archived=False))


class CampaignAdGroupState(BaseBulkActionView):
    @metrics_compat.timer("dash.api")
    def post(self, request, campaign_id):
        campaign = zemauth.access.get_campaign(request.user, Permission.WRITE, campaign_id)
        data = json.loads(request.body)

        state = data.get("state")
        if state is None or state not in constants.ContentAdSourceState.get_all():
            raise exc.ValidationError()

        ad_groups = helpers.get_selected_entities_post_request(models.AdGroup.objects, data, campaign_id=campaign.id)

        campaign_settings = campaign.get_current_settings()
        helpers.validate_ad_groups_state(ad_groups, campaign, campaign_settings, state)

        with transaction.atomic():
            for ad_group in ad_groups:
                self._update_adgroup(request, ad_group, state=state, skip_automation=True)

        if campaign.settings.autopilot:
            # TODO: RTAP: LEGACY
            if not ad_group.campaign.account.agency_uses_realtime_autopilot():
                autopilot_legacy.recalculate_budgets_campaign(campaign)
            else:
                autopilot.recalculate_ad_group_budgets(campaign)

        has_available_budget = data_helper.campaign_has_available_budget(campaign)
        editable_fields = {
            ad_group.id: breakdown_helpers.get_ad_group_editable_fields({"state": state}, has_available_budget)
            for ad_group in ad_groups
        }

        return self.create_api_response(
            {
                "rows": [
                    self.create_row(
                        ad_group.id,
                        stats={
                            "status": {"value": state},
                            "state": {
                                "value": state,
                                "isEditable": editable_fields[ad_group.id]["state"]["enabled"],
                                "editMessage": editable_fields[ad_group.id]["state"]["message"],
                            },
                        },
                    )
                    for ad_group in ad_groups
                ]
            }
        )

    def _update_adgroup(self, request, ad_group, **data):
        try:
            ad_group.settings.update(request, **data)

        except exc.MultipleValidationError as err:
            self._handle_multiple_error(ad_group, err)

        except (
            core.models.settings.ad_group_settings.exceptions.CannotChangeAdGroupState,
            core.models.settings.ad_group_settings.exceptions.AutopilotDailyBudgetTooLow,
            core.models.settings.ad_group_settings.exceptions.AutopilotDailyBudgetTooHigh,
        ) as err:
            raise exc.ValidationError("{}: {}".format(ad_group.settings.ad_group_name, str(err)))

    def _handle_multiple_error(self, ad_group, err):
        errors = []
        for e in err.errors:
            errors.append(str(e))
        raise exc.ValidationError("{}: {}".format(ad_group.settings.ad_group_name, ", ".join(errors)))


class AccountCampaignArchive(BaseBulkActionView):
    @metrics_compat.timer("dash.api")
    def post(self, request, account_id):
        account = zemauth.access.get_account(request.user, Permission.WRITE, account_id)

        campaigns = helpers.get_selected_entities_post_request(
            models.Campaign.objects, json.loads(request.body), account_id=account.id
        )

        with transaction.atomic():
            for campaign in campaigns:
                campaign.archive(request)

        return self.create_api_response(self.create_rows(campaigns, archived=True))


class AccountCampaignRestore(BaseBulkActionView):
    @metrics_compat.timer("dash.api")
    def post(self, request, account_id):
        account = zemauth.access.get_account(request.user, Permission.WRITE, account_id)

        campaigns = helpers.get_selected_entities_post_request(
            models.Campaign.objects, json.loads(request.body), include_archived=True, account_id=account.id
        )

        with transaction.atomic():
            for campaign in campaigns:
                campaign.restore(request)

        return self.create_api_response(self.create_rows(campaigns, archived=False))


class AllAccountsAccountArchive(BaseBulkActionView):
    @metrics_compat.timer("dash.api")
    def post(self, request):
        accounts = helpers.get_selected_entities_post_request(
            models.Account.objects.all().filter_by_entity_permission(request.user, Permission.WRITE),
            json.loads(request.body),
        )

        with transaction.atomic():
            for account in accounts:
                account.archive(request)

        return self.create_api_response(self.create_rows(accounts, archived=True))


class AllAccountsAccountRestore(BaseBulkActionView):
    @metrics_compat.timer("dash.api")
    def post(self, request):
        accounts = helpers.get_selected_entities_post_request(
            models.Account.objects.all().filter_by_entity_permission(request.user, Permission.WRITE),
            json.loads(request.body),
            include_archived=True,
        )

        with transaction.atomic():
            for account in accounts:
                account.restore(request)

        return self.create_api_response(self.create_rows(accounts, archived=False))
