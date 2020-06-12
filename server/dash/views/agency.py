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
from dash import constants
from dash import content_insights_helper
from dash import facebook_helper
from dash import forms
from dash import models
from dash.features import custom_flags
from dash.views import helpers
from prodops import hacks
from utils import api_common
from utils import dates_helper
from utils import email_helper
from utils import exc
from utils import slack
from utils import zlogging
from zemauth.models import User as ZemUser

logger = zlogging.getLogger(__name__)

CONVERSION_PIXEL_INACTIVE_DAYS = 7
CONTENT_INSIGHTS_TABLE_ROW_COUNT = 10
SUBAGENCY_MAP = {198: (196, 198)}


class ConversionPixel(api_common.BaseApiView):
    def get(self, request, account_id):
        account_id = int(account_id)
        account = helpers.get_account(request.user, account_id)

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

        account = helpers.get_account(request.user, account_id)  # check access to account

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
            helpers.get_account(request.user, conversion_pixel.account_id)  # check access to account
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


class AccountSettings(api_common.BaseApiView):
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        account_settings = account.get_current_settings()

        response = {
            "settings": self.get_dict(request, account_settings, account),
            "can_restore": account.can_restore(),
            "archived": account_settings.archived,
            "is_externally_managed": account.is_externally_managed,
        }

        self._add_agencies(request, response)

        if request.user.has_perm("zemauth.can_modify_account_manager"):
            response["account_managers"] = self.get_account_managers(request, account, account_settings)

        if request.user.has_perm("zemauth.can_set_account_sales_representative"):
            response["sales_reps"] = self.get_sales_representatives(account)
        if request.user.has_perm("zemauth.can_set_account_cs_representative"):
            response["cs_reps"] = self.get_cs_representatives(account)
        if request.user.has_perm("zemauth.can_set_account_ob_representative"):
            response["ob_reps"] = self.get_ob_representatives()
        if request.user.has_perm("zemauth.can_see_backend_hacks"):
            response["hacks"] = models.CustomHack.objects.all().filter_applied(account=account).filter_active(
                True
            ).to_dict_list() + custom_flags.helpers.get_all_custom_flags_on_account(account)

        if request.user.has_perm("zemauth.can_see_deals_in_ui"):
            response.update({"deals": helpers.get_applied_deals_dict(account.get_all_configured_deals())})

        return self.create_api_response(response)

    def put(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        resource = json.loads(request.body)

        form = forms.AccountSettingsForm(account, resource.get("settings", {}))
        settings = self.save_settings(request, account, form)
        response = {"settings": self.get_dict(request, settings, account), "can_restore": account.can_restore()}

        self._add_agencies(request, response)

        return self.create_api_response(response)

    def _add_agencies(self, request, response):
        if request.user.has_perm("zemauth.can_set_agency_for_account"):
            agencies = models.Agency.objects.filter(users__in=[request.user])
            if request.user.has_perm("zemauth.can_see_all_accounts"):
                agencies = models.Agency.objects.all()
            response["agencies"] = list(
                agencies.values(
                    "name",
                    "sales_representative",
                    "cs_representative",
                    "ob_sales_representative",
                    "ob_account_manager",
                    "default_account_type",
                )
            )

    def save_settings(self, request, account, form):
        old_name = account.name

        with transaction.atomic():
            # Form is additionally validated in self.set_allowed_sources method
            if not form.is_valid():
                data = self.get_validation_error_data(request, account)
                raise exc.ValidationError(errors=dict(form.errors), data=data)

            self._validate_essential_account_settings(request.user, form)

            self.set_account(request, account, form.cleaned_data)

            settings = account.get_current_settings().copy_settings()
            self.set_settings(settings, account, form.cleaned_data)

            if (
                "allowed_sources" in form.cleaned_data
                and form.cleaned_data["allowed_sources"] is not None
                and not request.user.has_perm("zemauth.can_modify_allowed_sources")
            ):
                raise exc.AuthorizationError()

            if "account_type" in form.cleaned_data and form.cleaned_data["account_type"]:
                if not request.user.has_perm("zemauth.can_modify_account_type"):
                    raise exc.AuthorizationError()
                settings.account_type = form.cleaned_data["account_type"]

            if "salesforce_url" in form.cleaned_data and form.cleaned_data["salesforce_url"]:
                if not request.user.has_perm("zemauth.can_see_salesforce_url"):
                    raise exc.AuthorizationError()
                settings.salesforce_url = form.cleaned_data["salesforce_url"]

            if "allowed_sources" in form.cleaned_data and form.cleaned_data["allowed_sources"] is not None:
                changes_text = self.set_allowed_sources(
                    settings, account, request.user.has_perm("zemauth.can_see_all_available_sources"), form
                )
                account.write_history(
                    changes_text, action_type=constants.HistoryActionType.SETTINGS_CHANGE, user=request.user
                )

            if "facebook_page" in form.data:
                if not request.user.has_perm("zemauth.can_modify_facebook_page"):
                    raise exc.AuthorizationError()
                facebook_account = self.get_or_create_facebook_account(account)
                self.set_facebook_page(facebook_account, form)
                facebook_account.save()

            if request.user.has_perm("zemauth.can_set_white_blacklist_publisher_groups"):
                if "whitelist_publisher_groups" in form.cleaned_data:
                    settings.whitelist_publisher_groups = form.cleaned_data["whitelist_publisher_groups"]
                if "blacklist_publisher_groups" in form.cleaned_data:
                    settings.blacklist_publisher_groups = form.cleaned_data["blacklist_publisher_groups"]

            if request.user.has_perm("zemauth.can_set_auto_add_new_sources"):
                if "auto_add_new_sources" in form.cleaned_data:
                    settings.auto_add_new_sources = form.cleaned_data["auto_add_new_sources"]

            if "frequency_capping" in form.cleaned_data and form.cleaned_data["frequency_capping"]:
                if not request.user.has_perm("zemauth.can_set_frequency_capping"):
                    raise exc.AuthorizationError()
                settings.frequency_capping = form.cleaned_data["frequency_capping"]

            account.save(request)
            settings.save(request, action_type=constants.HistoryActionType.SETTINGS_CHANGE)

            if account.name != old_name and "New account" in old_name:
                hacks.apply_account_create_hack(request, account)

                slack_msg = (
                    "Account #<https://one.zemanta.com/v2/analytics/account/{id}|{id}> {name} was created"
                    "{agency}.".format(
                        id=account.id,
                        name=account.name,
                        agency=" for agency {}".format(account.agency.name) if account.agency else "",
                    )
                )
                try:
                    slack.publish(text=slack_msg, channel=slack.CHANNEL_ZEM_FEED_NEW_ACCOUNTS)
                except Exception:
                    logger.exception("Connection error with Slack.")

            return settings

    def _validate_essential_account_settings(self, user, form):
        if (
            "default_sales_representative" in form.cleaned_data
            and form.cleaned_data["default_sales_representative"] is not None
            and not user.has_perm("zemauth.can_set_account_sales_representative")
        ):
            raise exc.AuthorizationError()

        if (
            "default_cs_representative" in form.cleaned_data
            and form.cleaned_data["default_cs_representative"] is not None
            and not user.has_perm("zemauth.can_set_account_cs_representative")
        ):
            raise exc.AuthorizationError()

        if (
            "ob_sales_representative" in form.cleaned_data
            and form.cleaned_data["ob_sales_representative"] is not None
            and not user.has_perm("zemauth.can_set_account_ob_representative")
        ):
            raise exc.AuthorizationError()

        if (
            "ob_account_manager" in form.cleaned_data
            and form.cleaned_data["ob_account_manager"] is not None
            and not user.has_perm("zemauth.can_set_account_ob_representative")
        ):
            raise exc.AuthorizationError()

        if (
            "name" in form.cleaned_data
            and form.cleaned_data["name"] is not None
            and not user.has_perm("zemauth.can_modify_account_name")
        ):
            raise exc.AuthorizationError()

        if (
            "default_account_manager" in form.cleaned_data
            and form.cleaned_data["default_account_manager"] is not None
            and not user.has_perm("zemauth.can_modify_account_manager")
        ):
            raise exc.AuthorizationError()

    def get_validation_error_data(self, request, account):
        data = {}
        if not request.user.has_perm("zemauth.can_modify_allowed_sources"):
            return data

        data["allowed_sources"] = self.get_allowed_sources(
            account,
            request.user.has_perm("zemauth.can_see_all_available_sources"),
            [source.id for source in account.allowed_sources.all()],
        )
        return data

    def set_account(self, request, account, resource):
        if resource["name"]:
            account.name = resource["name"]
        if resource["currency"]:
            account.currency = resource["currency"]
        if resource["agency"]:
            if not request.user.has_perm("zemauth.can_set_agency_for_account"):
                raise exc.AuthorizationError()

            try:
                agency = models.Agency.objects.get(name=resource["agency"])
                account.agency = agency
                if not account.yahoo_account:
                    account.yahoo_account = agency.yahoo_account
            except models.Agency.DoesNotExist:
                if not request.user.has_perm("zemauth.can_create_agency"):
                    raise exc.AuthorizationError()
                agency = models.Agency.objects.create(
                    request,
                    name=resource["agency"],
                    sales_representative=resource["default_sales_representative"],
                    cs_representative=resource["default_cs_representative"],
                    ob_sales_representative=resource["ob_sales_representative"],
                    ob_account_manager=resource["ob_account_manager"],
                )
                account.agency = agency

    def get_non_removable_sources(self, account, sources_to_be_removed):
        return list(
            models.AdGroupSource.objects.all()
            .filter(settings__state=constants.AdGroupSourceSettingsState.ACTIVE)
            .filter(ad_group__settings__state=constants.AdGroupSettingsState.ACTIVE)
            .filter(ad_group__campaign__account=account.id)
            .filter(source__in=sources_to_be_removed)
            .values_list("source_id", flat=True)
            .distinct()
        )

    def add_error_to_account_agency_form(self, form, to_be_removed):
        source_names = [source.name for source in models.Source.objects.filter(id__in=to_be_removed).order_by("id")]
        media_sources = ", ".join(source_names)
        if len(source_names) > 1:
            msg = "Can't save changes because media sources {} are still used on this account.".format(media_sources)
        else:
            msg = "Can't save changes because media source {} is still used on this account.".format(media_sources)

        form.add_error("allowed_sources", msg)

    def set_allowed_sources(self, settings, account, can_see_all_available_sources, account_agency_form):
        allowed_sources_dict = account_agency_form.cleaned_data.get("allowed_sources")

        if not allowed_sources_dict:
            return

        all_available_sources = self.get_all_media_sources(account, can_see_all_available_sources)
        current_allowed_sources = self.get_allowed_media_sources(account, can_see_all_available_sources)
        new_allowed_sources = self.filter_allowed_sources_dict(all_available_sources, allowed_sources_dict)

        new_allowed_sources_set = set(new_allowed_sources)
        current_allowed_sources_set = set(current_allowed_sources)

        to_be_removed = current_allowed_sources_set.difference(new_allowed_sources_set)
        to_be_added = new_allowed_sources_set.difference(current_allowed_sources_set)

        non_removable_sources = self.get_non_removable_sources(account, to_be_removed)
        if len(non_removable_sources) > 0:
            self.add_error_to_account_agency_form(account_agency_form, non_removable_sources)
            return

        changes_text = None
        if to_be_added or to_be_removed:
            changes_text = self.get_changes_text_for_media_sources(to_be_added, to_be_removed)
            account.allowed_sources.add(*list(to_be_added))
            account.allowed_sources.remove(*list(to_be_removed))
        return changes_text

    def get_or_create_facebook_account(self, account):
        try:
            facebook_account = account.facebookaccount
        except models.FacebookAccount.DoesNotExist:
            facebook_account = models.FacebookAccount.objects.create(
                account=account, status=constants.FacebookPageRequestType.EMPTY
            )
        return facebook_account

    def set_facebook_page(self, facebook_account, form):
        new_url = form.cleaned_data["facebook_page"]
        credentials = facebook_helper.get_credentials()
        facebook_helper.update_facebook_account(
            facebook_account, new_url, credentials["business_id"], credentials["access_token"]
        )

    def get_all_media_sources(self, account, can_see_all_available_sources):
        if account.agency and account.agency.allowed_sources.count() > 0:
            return list(account.agency.allowed_sources.all())
        qs_sources = models.Source.objects.all()
        if not can_see_all_available_sources:
            qs_sources = qs_sources.filter(released=True)

        return list(qs_sources)

    def get_allowed_media_sources(self, account, can_see_all_available_sources):
        qs_allowed_sources = account.allowed_sources.all()
        if not can_see_all_available_sources:
            qs_allowed_sources = qs_allowed_sources.filter(released=True)

        return list(qs_allowed_sources)

    def filter_allowed_sources_dict(self, sources, allowed_sources_dict):
        allowed_sources = []
        for source in sources:
            if source.id in allowed_sources_dict:
                value = allowed_sources_dict[source.id]
                if value.get("allowed", False):
                    allowed_sources.append(source)

        return allowed_sources

    def set_settings(self, settings, account, resource):
        settings.account = account
        if resource["name"]:
            settings.name = resource["name"]
        if resource["default_account_manager"]:
            settings.default_account_manager = resource["default_account_manager"]
        if resource["default_sales_representative"]:
            settings.default_sales_representative = resource["default_sales_representative"]
        if resource["default_cs_representative"]:
            settings.default_cs_representative = resource["default_cs_representative"]
        if resource["ob_sales_representative"]:
            settings.ob_sales_representative = resource["ob_sales_representative"]
        if resource["ob_account_manager"]:
            settings.ob_account_manager = resource["ob_account_manager"]

    def get_allowed_sources(self, account, include_unreleased_sources, allowed_sources_ids_list):
        allowed_sources_dict = {}

        all_sources_queryset = models.Source.objects.all()
        if account.agency and account.agency.allowed_sources.count() > 0:
            all_sources_queryset = account.agency.allowed_sources.all()
        if not include_unreleased_sources:
            all_sources_queryset = all_sources_queryset.filter(released=True)

        all_sources = list(all_sources_queryset)

        for source in all_sources:
            if source.id not in allowed_sources_ids_list and source.deprecated:
                continue

            source_settings = {"name": source.name, "released": source.released, "deprecated": source.deprecated}
            if source.id in allowed_sources_ids_list:
                source_settings["allowed"] = True
            allowed_sources_dict[source.id] = source_settings

        return allowed_sources_dict

    def add_facebook_account_to_result(self, result, account):
        try:
            result["facebook_page"] = account.facebookaccount.page_url
            result["facebook_status"] = models.constants.FacebookPageRequestType.get_text(
                account.facebookaccount.status
            )
        except models.FacebookAccount.DoesNotExist:
            result["facebook_status"] = models.constants.FacebookPageRequestType.get_text(
                models.constants.FacebookPageRequestType.EMPTY
            )

    def get_dict(self, request, settings, account):
        if not settings:
            return {}

        result = {"id": str(account.pk), "archived": settings.archived, "currency": account.currency}
        if request.user.has_perm("zemauth.can_modify_account_name"):
            result["name"] = account.name
        if request.user.has_perm("zemauth.can_modify_account_manager"):
            result["default_account_manager"] = (
                str(settings.default_account_manager.id) if settings.default_account_manager is not None else None
            )
        if request.user.has_perm("zemauth.can_set_account_sales_representative"):
            result["default_sales_representative"] = (
                str(settings.default_sales_representative.id)
                if settings.default_sales_representative is not None
                else None
            )
        if request.user.has_perm("zemauth.can_set_account_cs_representative"):
            result["default_cs_representative"] = (
                str(settings.default_cs_representative.id) if settings.default_cs_representative is not None else None
            )
        if request.user.has_perm("zemauth.can_set_account_ob_representative"):
            result["ob_sales_representative"] = (
                str(settings.ob_sales_representative_id) if settings.ob_sales_representative_id else None
            )
        if request.user.has_perm("zemauth.can_set_account_ob_representative"):
            result["ob_account_manager"] = (
                str(settings.ob_account_manager_id) if settings.ob_account_manager_id else None
            )
        if request.user.has_perm("zemauth.can_modify_account_type"):
            result["account_type"] = settings.account_type
        if request.user.has_perm("zemauth.can_modify_allowed_sources"):
            result["allowed_sources"] = self.get_allowed_sources(
                account,
                request.user.has_perm("zemauth.can_see_all_available_sources"),
                [source.id for source in account.allowed_sources.all()],
            )
        if request.user.has_perm("zemauth.can_modify_facebook_page"):
            self.add_facebook_account_to_result(result, account)
        if request.user.has_perm("zemauth.can_set_agency_for_account"):
            if account.agency:
                result["agency"] = account.agency.name
            else:
                result["agency"] = ""
        if request.user.has_perm("zemauth.can_see_salesforce_url"):
            result["salesforce_url"] = settings.salesforce_url
        if request.user.has_perm("zemauth.can_set_auto_add_new_sources"):
            result["auto_add_new_sources"] = settings.auto_add_new_sources

        result["whitelist_publisher_groups"] = settings.whitelist_publisher_groups
        result["blacklist_publisher_groups"] = settings.blacklist_publisher_groups

        if request.user.has_perm("zemauth.can_set_frequency_capping"):
            result["frequency_capping"] = settings.frequency_capping

        return result

    def get_changes_text_for_media_sources(self, added_sources, removed_sources):
        sources_text_list = []
        if added_sources:
            added_sources_names = [source.name for source in added_sources]
            added_sources_text = "Added allowed media sources ({})".format(", ".join(added_sources_names))
            sources_text_list.append(added_sources_text)

        if removed_sources:
            removed_sources_names = [source.name for source in removed_sources]
            removed_sources_text = "Removed allowed media sources ({})".format(", ".join(removed_sources_names))
            sources_text_list.append(removed_sources_text)

        return ", ".join(sources_text_list)

    def get_account_managers(self, request, account, settings):
        users = helpers.get_users_for_manager(request.user, account, settings.default_account_manager)
        return self.format_user_list(users)

    def get_sales_representatives(self, account):
        users = ZemUser.objects.get_users_with_perm("campaign_settings_sales_rep").filter(is_active=True)
        if account.agency_id in SUBAGENCY_MAP:
            subagencies = models.Agency.objects.filter(pk__in=SUBAGENCY_MAP[account.agency_id])
            users &= ZemUser.objects.filter(agency__in=subagencies).distinct()
        return self.format_user_list(users)

    def get_cs_representatives(self, account):
        users = ZemUser.objects.get_users_with_perm("campaign_settings_cs_rep").filter(is_active=True)
        if account.agency_id in SUBAGENCY_MAP:
            subagencies = models.Agency.objects.filter(pk__in=SUBAGENCY_MAP[account.agency_id])
            users &= ZemUser.objects.filter(agency__in=subagencies).distinct()
        return self.format_user_list(users)

    def get_ob_representatives(self):
        users = ZemUser.objects.get_users_with_perm("can_be_ob_representative").filter(is_active=True)
        return self.format_user_list(users)

    def format_user_list(self, users):
        return [{"id": str(user.id), "name": helpers.get_user_full_name_or_email(user)} for user in users]


class AccountUsers(api_common.BaseApiView):
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


class AccountUserAction(api_common.BaseApiView):
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


class CampaignContentInsights(api_common.BaseApiView):
    @newrelic.agent.function_trace()
    def get(self, request, campaign_id):
        if not request.user.has_perm("zemauth.can_view_campaign_content_insights_side_tab"):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id)
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


class History(api_common.BaseApiView):
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
            entity_filter["ad_group"] = helpers.get_ad_group(request.user, int(ad_group_raw))
        campaign_raw = request.GET.get("campaign")
        if campaign_raw:
            entity_filter["campaign"] = helpers.get_campaign(request.user, int(campaign_raw))
        account_raw = request.GET.get("account")
        if account_raw:
            entity_filter["account"] = helpers.get_account(request.user, int(account_raw))
        agency_raw = request.GET.get("agency")
        if agency_raw:
            entity_filter["agency"] = helpers.get_agency(request.user, int(agency_raw))
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


class Agencies(api_common.BaseApiView):
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


class FacebookAccountStatus(api_common.BaseApiView):
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        credentials = facebook_helper.get_credentials()
        try:
            pages = facebook_helper.get_all_pages(credentials["business_id"], credentials["access_token"])
            if pages is None:
                raise exc.BaseError("Error while accessing facebook page api.")
            page_status = pages.get(account.facebookaccount.page_id)
            account_status = self._get_account_status(page_status)
        except models.FacebookAccount.DoesNotExist:
            account_status = models.constants.FacebookPageRequestType.EMPTY
        except exc.BaseError:
            account_status = models.constants.FacebookPageRequestType.ERROR

        account_status_as_string = models.constants.FacebookPageRequestType.get_text(account_status)
        return self.create_api_response({"status": account_status_as_string})

    @staticmethod
    def _get_account_status(page_status):
        if page_status is None:
            return models.constants.FacebookPageRequestType.EMPTY
        elif page_status == "CONFIRMED":
            return models.constants.FacebookPageRequestType.CONNECTED
        elif page_status == "PENDING":
            return models.constants.FacebookPageRequestType.PENDING
        else:
            return models.constants.FacebookPageRequestType.INVALID
