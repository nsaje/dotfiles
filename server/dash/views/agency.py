import functools
import json
import re

import newrelic.agent
from django.conf import settings
from django.db.models import Q

import core.common
import core.features.goals
import core.features.goals.campaign_goal.exceptions
import core.features.goals.conversion_goal.exceptions
import core.features.multicurrency
import core.models.ad_group.exceptions
import core.models.conversion_pixel.exceptions
import core.models.settings.ad_group_settings.exceptions
import core.models.settings.ad_group_source_settings.exceptions
import core.models.settings.campaign_settings.exceptions
import utils.exc
import zemauth.access
from dash import constants
from dash import content_insights_helper
from dash import forms
from dash import models
from dash.common.views_base import DASHAPIBaseView
from dash.views import helpers
from utils import dates_helper
from utils import exc
from utils import zlogging
from zemauth.features.entity_permission import Permission

logger = zlogging.getLogger(__name__)

CONVERSION_PIXEL_INACTIVE_DAYS = 7
CONTENT_INSIGHTS_TABLE_ROW_COUNT = 10


class AdGroupSettingsState(DASHAPIBaseView):
    def post(self, request, ad_group_id):
        ad_group = zemauth.access.get_ad_group(request.user, Permission.WRITE, ad_group_id)
        data = json.loads(request.body)
        new_state = data.get("state")

        campaign_settings = ad_group.campaign.get_current_settings()
        helpers.validate_ad_groups_state([ad_group], ad_group.campaign, campaign_settings, new_state)

        try:
            ad_group.settings.update(request, state=new_state)

        except core.models.settings.ad_group_settings.exceptions.CannotChangeAdGroupState as err:
            raise utils.exc.ValidationError(error={"state": [str(err)]})

        return self.create_api_response({"id": str(ad_group.pk), "state": new_state})


class ConversionPixel(DASHAPIBaseView):
    def get(self, request, account_id):
        account_id = int(account_id)
        account = zemauth.access.get_account(request.user, Permission.READ, account_id)

        audience_enabled_only = request.GET.get("audience_enabled_only", "") == "1"

        pixels = models.ConversionPixel.objects.filter(account=account)
        if audience_enabled_only:
            pixels = pixels.filter(Q(audience_enabled=True) | Q(additional_pixel=True))

        yesterday = dates_helper.local_yesterday()
        rows = [self._format_pixel(pixel, request.user, date=yesterday) for pixel in pixels]

        return self.create_api_response(
            {"rows": rows, "conversion_pixel_tag_prefix": settings.CONVERSION_PIXEL_PREFIX + str(account.id) + "/"}
        )

    def post(self, request, account_id):
        account_id = int(account_id)

        account = zemauth.access.get_account(request.user, Permission.WRITE, account_id)

        try:
            data = json.loads(request.body)
        except ValueError:
            raise exc.ValidationError()

        form = forms.ConversionPixelCreateForm(data)
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        pixel_create_fn = functools.partial(models.ConversionPixel.objects.create, request, account, **data)
        conversion_pixel = self._update_pixel(pixel_create_fn)

        return self.create_api_response(self._format_pixel(conversion_pixel, request.user))

    def put(self, request, conversion_pixel_id):
        try:
            conversion_pixel = models.ConversionPixel.objects.get(id=conversion_pixel_id)
        except models.ConversionPixel.DoesNotExist:
            raise exc.MissingDataError("Conversion pixel does not exist")

        try:
            zemauth.access.get_account(request.user, Permission.WRITE, conversion_pixel.account_id)
        except exc.MissingDataError:
            raise exc.MissingDataError("Conversion pixel does not exist")

        try:
            data = json.loads(request.body)
        except ValueError:
            raise exc.ValidationError()

        form = forms.ConversionPixelForm(data)
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        pixel_update_fn = functools.partial(conversion_pixel.update, request, **data)
        self._update_pixel(pixel_update_fn)

        return self.create_api_response(self._format_pixel(conversion_pixel, request.user))

    def _update_pixel(self, pixel_update_fn):
        try:
            return pixel_update_fn()

        except core.models.conversion_pixel.exceptions.DuplicatePixelName as err:
            raise utils.exc.ValidationError(errors={"name": [str(err)]})

        except core.models.conversion_pixel.exceptions.AudiencePixelAlreadyExists as err:
            raise utils.exc.ValidationError(errors={"audience_enabled": str(err)})

        except core.models.conversion_pixel.exceptions.AudiencePixelCanNotBeArchived as err:
            raise utils.exc.ValidationError(errors={"audience_enabled": str(err)})

        except core.models.conversion_pixel.exceptions.MutuallyExclusivePixelFlagsEnabled as err:
            raise utils.exc.ValidationError(errors={"additional_pixel": [str(err)]})

        except core.models.conversion_pixel.exceptions.AudiencePixelNotSet as err:
            raise utils.exc.ValidationError(errors={"additional_pixel": [str(err)]})

        except core.common.entity_limits.EntityLimitExceeded as err:
            raise utils.exc.ForbiddenError(message=[str(err)])

    def _format_pixel(self, pixel, user, date=None):
        data = {
            "id": pixel.id,
            "name": pixel.name,
            "url": pixel.get_url(),
            "audience_enabled": pixel.audience_enabled,
            "additional_pixel": pixel.additional_pixel,
            "archived": pixel.archived,
            "last_triggered": pixel.last_triggered,
            "impressions": pixel.get_impressions(date=date),
            "notes": pixel.notes,
        }

        if user.has_perm("zemauth.can_redirect_pixels"):
            data["redirect_url"] = pixel.redirect_url

        return data


class CampaignContentInsights(DASHAPIBaseView):
    @newrelic.agent.function_trace()
    def get(self, request, campaign_id):
        campaign = zemauth.access.get_campaign(request.user, Permission.READ, campaign_id)
        view_filter = forms.ViewFilterForm(request.GET)
        if not view_filter.is_valid():
            raise exc.ValidationError(errors=dict(view_filter.errors))
        start_date = view_filter.cleaned_data.get("start_date")
        end_date = view_filter.cleaned_data.get("end_date")

        best_performer_rows, worst_performer_rows = content_insights_helper.fetch_campaign_content_ad_metrics(
            request.user, campaign, start_date, end_date
        )
        return self.create_api_response(
            {
                "summary": "Title",
                "metric": "CTR",
                "best_performer_rows": best_performer_rows,
                "worst_performer_rows": worst_performer_rows,
            }
        )


class History(DASHAPIBaseView):
    def get(self, request):
        # in case somebody wants to fetch entire history disallow it for the
        # moment
        entity_filter = self._extract_entity_filter(request)
        if not set(entity_filter.keys()).intersection({"ad_group", "campaign", "account", "agency"}):
            raise exc.MissingDataError()
        order = self._extract_order(request)
        response = {"history": self.get_history(entity_filter, order=order)}
        return self.create_api_response(response)

    def _extract_entity_filter(self, request):
        entity_filter = {}
        ad_group_raw = request.GET.get("ad_group")
        if ad_group_raw:
            entity_filter["ad_group"] = zemauth.access.get_ad_group(request.user, Permission.READ, int(ad_group_raw))
        campaign_raw = request.GET.get("campaign")
        if campaign_raw:
            entity_filter["campaign"] = zemauth.access.get_campaign(request.user, Permission.READ, int(campaign_raw))
        account_raw = request.GET.get("account")
        if account_raw:
            entity_filter["account"] = zemauth.access.get_account(request.user, Permission.READ, int(account_raw))
        agency_raw = request.GET.get("agency")
        if agency_raw:
            entity_filter["agency"] = zemauth.access.get_agency(request.user, Permission.READ, int(agency_raw))
        level_raw = request.GET.get("level")
        if level_raw and int(level_raw) in constants.HistoryLevel.get_all():
            entity_filter["level"] = int(level_raw)
        return entity_filter

    def _extract_order(self, request):
        order = ["-created_dt"]
        order_raw = request.GET.get("order") or ""
        if re.match("[-]?(created_dt|created_by)", order_raw):
            order = [order_raw]
        return order

    def get_history(self, filters, order=["-created_dt"]):
        history_entries = models.History.objects.filter(**filters).order_by(*order).select_related("created_by")

        history = []
        for history_entry in history_entries:
            history.append(
                {
                    "datetime": history_entry.created_dt,
                    "changed_by": history_entry.get_changed_by_text(),
                    "changes_text": history_entry.changes_text,
                }
            )
        return history


class Agencies(DASHAPIBaseView):
    def get(self, request):
        agencies = models.Agency.objects.filter_by_entity_permission(request.user, Permission.READ).values(
            "id", "name", "is_externally_managed"
        )

        return self.create_api_response(
            {
                "agencies": [
                    {
                        "id": str(agency["id"]),
                        "name": agency["name"],
                        "is_externally_managed": agency["is_externally_managed"],
                    }
                    for agency in agencies
                ]
            }
        )
