import functools
import json
import re

import newrelic.agent
from django.conf import settings
from django.contrib.auth import models as authmodels
from django.db import transaction
from django.db.models import Q
from django.http import Http404

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
from prodops import hacks
from utils import dates_helper
from utils import email_helper
from utils import exc
from utils import zlogging
from zemauth.features.entity_permission import Permission
from zemauth.models import User as ZemUser

logger = zlogging.getLogger(__name__)

CONVERSION_PIXEL_INACTIVE_DAYS = 7
CONTENT_INSIGHTS_TABLE_ROW_COUNT = 10


class AdGroupSettingsState(DASHAPIBaseView):
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        current_settings = ad_group.get_current_settings()
        return self.create_api_response({"id": str(ad_group.pk), "state": current_settings.state})

    def post(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
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

    def _format_pixel(self, pixel, user, date=None):
        data = {
            "id": pixel.id,
            "name": pixel.name,
            "url": pixel.get_url(),
            "audience_enabled": pixel.audience_enabled,
            "additional_pixel": pixel.additional_pixel,
            "archived": pixel.archived,
        }
        if user.has_perm("zemauth.can_see_pixel_traffic"):
            data["last_triggered"] = pixel.last_triggered
            data["impressions"] = pixel.get_impressions(date=date)
        if user.has_perm("zemauth.can_redirect_pixels"):
            data["redirect_url"] = pixel.redirect_url
        if user.has_perm("zemauth.can_see_pixel_notes"):
            data["notes"] = pixel.notes
        return data


class AccountUsers(DASHAPIBaseView):
    def get(self, request, account_id):
        if not request.user.has_perm("zemauth.account_agency_access_permissions"):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        agency_users = account.agency.users.all() if account.agency else []

        users = [self._get_user_dict(u) for u in account.users.all()]
        agency_managers = [self._get_user_dict(u, agency_managers=True) for u in agency_users]

        if request.user.has_perm("zemauth.can_see_agency_managers_under_access_permissions"):
            users = agency_managers + users

        return self.create_api_response(
            {"users": users, "agency_managers": agency_managers if account.agency else None}
        )

    def put(self, request, account_id):
        if not request.user.has_perm("zemauth.account_agency_access_permissions"):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        resource = json.loads(request.body)

        form = forms.UserForm(resource)
        is_valid = form.is_valid()

        # in case the user already exists and form contains
        # first name and last name, error is returned. In case
        # the form only contains email, user is added to the account.
        if form.cleaned_data.get("email") is None:
            self._raise_validation_error(form.errors)

        first_name = form.cleaned_data.get("first_name")
        last_name = form.cleaned_data.get("last_name")
        email = form.cleaned_data.get("email")

        try:

            user = ZemUser.objects.get(email__iexact=email)

            if (first_name == user.first_name and last_name == user.last_name) or (not first_name and not last_name):
                created = False
            else:
                self._raise_validation_error(
                    form.errors,
                    message='The user with e-mail {} is already registred as "{}". '
                    "Please contact technical support if you want to change the user's "
                    "name or leave first and last names blank if you just want to add "
                    "access to the account for this user.".format(user.email, user.get_full_name()),
                )
        except ZemUser.DoesNotExist:
            if not is_valid:
                self._raise_validation_error(form.errors)

            user = ZemUser.objects.create_user(email, first_name=first_name, last_name=last_name)
            self._add_user_to_groups(user)
            hacks.apply_create_user_hacks(user, account)
            email_helper.send_email_to_new_user(user, request, agency=account.agency)

            created = True

        # we check account for this user to prevent multiple additions
        if not len(account.users.filter(pk=user.pk)):
            account.users.add(user)

            changes_text = "Added user {} ({})".format(user.get_full_name(), user.email)

            # add history entry
            new_settings = account.get_current_settings().copy_settings()
            new_settings.changes_text = changes_text
            new_settings.save(request, changes_text=changes_text)

            user.refresh_entity_permissions()

        return self.create_api_response({"user": self._get_user_dict(user)}, status_code=201 if created else 200)

    def _add_user_to_groups(self, user):
        perm = authmodels.Permission.objects.get(codename="this_is_public_group")
        group = authmodels.Group.objects.get(permissions=perm)
        group.user_set.add(user)

    def _raise_validation_error(self, errors, message=None):
        raise exc.ValidationError(
            errors=dict(errors), pretty_message=message or "Please specify the user's first name, last name and email."
        )

    def delete(self, request, account_id, user_id):
        if not request.user.has_perm("zemauth.account_agency_access_permissions"):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        remove_from_all_accounts = request.GET.get("remove_from_all_accounts")
        try:
            user = ZemUser.objects.get(pk=user_id)
        except ZemUser.DoesNotExist:
            raise exc.MissingDataError()

        with transaction.atomic():
            self._remove_user(request, account, user, remove_from_all_accounts=remove_from_all_accounts)

        user.refresh_entity_permissions()
        return self.create_api_response({"user_id": user.id})

    def _remove_user(self, request, account, user, remove_from_all_accounts=False):
        is_agency_manager = account.agency and account.agency.users.filter(pk=user.pk).exists()

        if account.agency and (is_agency_manager or remove_from_all_accounts):
            all_agency_accounts = account.agency.account_set.all()
            for account in all_agency_accounts:
                self._remove_user_from_account(account, user, request.user)

            account.agency.users.remove(user)
            changes_text = "Removed agency user {} ({})".format(user.get_full_name(), user.email)
            account.agency.write_history(changes_text, user=request.user)
            if user.agency_set.count() < 2:
                group = authmodels.Group.objects.get(
                    permissions=authmodels.Permission.objects.get(codename="this_is_agency_manager_group")
                )
                user.groups.remove(group)
        else:
            self._remove_user_from_account(account, user, request.user)

    def _remove_user_from_account(self, account, removed_user, request_user):
        if len(account.users.filter(pk=removed_user.pk)):
            account.users.remove(removed_user)
            changes_text = "Removed user {} ({})".format(removed_user.get_full_name(), removed_user.email)
            account.write_history(changes_text, user=request_user)

    def _get_user_dict(self, user, agency_managers=False):
        return {
            "id": user.id,
            "name": user.get_full_name(),
            "email": user.email,
            "last_login": user.last_login and user.last_login.date(),
            "is_active": not user.last_login or user.last_login != user.date_joined,
            "is_agency_manager": agency_managers,
            "can_use_restapi": user.has_perm("zemauth.can_use_restapi"),
        }


class AccountUserAction(DASHAPIBaseView):
    ACTIVATE = "activate"
    PROMOTE = "promote"
    DOWNGRADE = "downgrade"
    ENABLE_API = "enable_api"

    def __init__(self):
        self.actions = {
            AccountUserAction.ACTIVATE: self._activate,
            AccountUserAction.PROMOTE: self._promote,
            AccountUserAction.DOWNGRADE: self._downgrade,
            AccountUserAction.ENABLE_API: self._enable_api,
        }
        self.permissions = {
            AccountUserAction.ACTIVATE: "zemauth.account_agency_access_permissions",
            AccountUserAction.PROMOTE: "zemauth.can_promote_agency_managers",
            AccountUserAction.DOWNGRADE: "zemauth.can_promote_agency_managers",
            AccountUserAction.ENABLE_API: "zemauth.can_manage_restapi_access",
        }

    def post(self, request, account_id, user_id, action):
        if action not in self.actions:
            raise Http404("Action does not exist")

        if not request.user.has_perm(self.permissions[action]):
            raise exc.AuthorizationError()
        account = helpers.get_account(request.user, account_id)

        try:
            user = ZemUser.objects.get(pk=user_id)
        except ZemUser.DoesNotExist:
            raise exc.ValidationError(pretty_message="Cannot {action} nonexisting user.".format(action=action))
        if user not in account.users.all() and (not account.is_agency() or user not in account.agency.users.all()):
            raise exc.AuthorizationError()

        self.actions[action](request, user, account)
        user.refresh_entity_permissions()

        return self.create_api_response()

    def _activate(self, request, user, account):
        email_helper.send_email_to_new_user(user, request)

        changes_text = "Resent activation mail {} ({})".format(user.get_full_name(), user.email)
        account.write_history(changes_text, user=request.user)

    def _promote(self, request, user, account):
        group = self._get_agency_manager_group()

        self._check_is_agency_account(account)

        account.agency.users.add(user)
        account.users.remove(user)
        user.groups.add(group)

    def _downgrade(self, request, user, account):
        group = self._get_agency_manager_group()

        self._check_is_agency_account(account)
        self._check_user_in_multiple_agencies(user)

        account.agency.users.remove(user)
        account.users.add(user)
        user.groups.remove(group)

    def _enable_api(self, request, user, account):
        perm = authmodels.Permission.objects.get(codename="this_is_restapi_group")
        api_group = authmodels.Group.objects.get(permissions=perm)

        if api_group not in user.groups.all():
            user.groups.add(api_group)
            changes_text = "{} was granted REST API access".format(user.email)
            account.write_history(changes_text=changes_text)
            email_helper.send_restapi_access_enabled_notification(user)

    def _check_is_agency_account(self, account):
        if not account.is_agency():
            raise exc.ValidationError(pretty_message="Cannot promote user on account without agency.")

    def _check_user_in_multiple_agencies(self, user):
        if user.agency_set.count() > 1:
            raise exc.ValidationError(pretty_message="Cannot downgrade user set on multiple agencies.")

    def _get_agency_manager_group(self):
        perm = authmodels.Permission.objects.get(codename="this_is_agency_manager_group")
        return authmodels.Group.objects.get(permissions=perm)


class CampaignContentInsights(DASHAPIBaseView):
    @newrelic.agent.function_trace()
    def get(self, request, campaign_id):
        if not request.user.has_perm("zemauth.can_view_campaign_content_insights_side_tab"):
            raise exc.AuthorizationError()

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
        if not request.user.has_perm("zemauth.can_view_new_history_backend"):
            raise exc.AuthorizationError()
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
        if not request.user.has_perm("zemauth.can_filter_by_agency"):
            raise exc.AuthorizationError()

        agencies = list(
            models.Agency.objects.all().filter_by_user(request.user).values("id", "name", "is_externally_managed")
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
