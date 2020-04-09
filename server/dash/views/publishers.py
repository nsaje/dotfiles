import json
import os

import slugify
from django.conf import settings
from django.db.models import Count
from django.db.models import Q

import core.features.publisher_groups

from dash import forms
from dash import models
from dash.views import helpers
from utils import api_common
from utils import exc
from utils import s3helpers


def serialize_publisher_group(publisher_group):
    type_, level, obj, obj_name = core.features.publisher_groups.parse_default_publisher_group_origin(publisher_group)
    if hasattr(publisher_group, "num_entries"):
        entries_count = publisher_group.num_entries
    else:
        entries_count = publisher_group.entries.all().count()
    return {
        "id": publisher_group.id,
        "agency_id": str(publisher_group.agency.id) if publisher_group.agency else None,
        "account_id": str(publisher_group.account.id) if publisher_group.account else None,
        "name": publisher_group.name,
        "include_subdomains": publisher_group.default_include_subdomains,
        "implicit": publisher_group.implicit,
        "size": entries_count,
        "modified": publisher_group.modified_dt,
        "created": publisher_group.created_dt,
        "type": type_,
        "level": level,
        "level_name": obj_name,
        "level_id": obj.id if obj else None,
    }


class PublisherTargeting(api_common.BaseApiView):
    def post(self, request):
        if not request.user.has_perm("zemauth.can_modify_publisher_blacklist_status"):
            raise exc.MissingDataError()
        resource = json.loads(request.body)
        form = forms.PublisherTargetingForm(request.user, resource)
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        obj = form.get_publisher_group_level_obj()
        if not core.features.publisher_groups.can_user_handle_publisher_listing_level(request.user, obj):
            raise exc.AuthorizationError()

        entry_dicts = form.cleaned_data["entries"]

        if entry_dicts:
            core.features.publisher_groups.handle_publishers(request, entry_dicts, obj, form.cleaned_data["status"])

        response = {"success": True}
        return self.create_api_response(response)


class PublisherGroups(api_common.BaseApiView):
    def get(self, request):
        if not request.user.has_perm("zemauth.can_edit_publisher_groups"):
            raise exc.MissingDataError()

        agency_id = request.GET.get("agency_id")
        account_id = request.GET.get("account_id")

        if account_id is not None:
            account = helpers.get_account(request.user, account_id)
            publisher_groups_q = models.PublisherGroup.objects.filter_by_account(account).annotate(
                num_entries=Count("entries")
            )
        elif agency_id is not None:
            agency = helpers.get_agency(request.user, agency_id)
            publisher_groups_q = models.PublisherGroup.objects.filter(
                Q(agency=agency) | Q(account__agency=agency)
            ).annotate(num_entries=Count("entries"))
        else:
            raise exc.ValidationError(errors={"non_field_errors": "Either agency id or account id must be provided."})

        if request.GET.get("not_implicit"):
            publisher_groups_q = publisher_groups_q.filter(implicit=False)

        publisher_groups = []
        for pg in publisher_groups_q:
            publisher_groups.append(serialize_publisher_group(pg))

        return self.create_api_response({"publisher_groups": publisher_groups, "success": True})


class PublisherGroupsUpload(api_common.BaseApiView):
    def get(self, request, csv_key):
        # download errors csv
        if not request.user.has_perm("zemauth.can_edit_publisher_groups"):
            raise exc.MissingDataError()

        agency_id = request.GET.get("agency_id")
        account_id = request.GET.get("account_id")

        if agency_id is None and account_id is None:
            raise exc.ValidationError(
                errors={
                    "account_id": ["One of either account or agency must be set."],
                    "agency_id": ["One of either account or agency must be set."],
                }
            )

        account = helpers.get_account(request.user, account_id) if account_id is not None else None
        agency = helpers.get_agency(request.user, agency_id) if agency_id is not None else None

        s3_helper = s3helpers.S3Helper(settings.S3_BUCKET_PUBLISHER_GROUPS)

        if account is not None:
            content = s3_helper.get(
                os.path.join("publisher_group_errors", "account_{}".format(account.id), csv_key + ".csv")
            )
        elif agency is not None:
            content = s3_helper.get(
                os.path.join("publisher_group_errors", "agency_{}".format(agency.id), csv_key + ".csv")
            )

        return self.create_csv_response("publisher_group_errors", content=content)

    def post(self, request):
        if not request.user.has_perm("zemauth.can_edit_publisher_groups"):
            raise exc.MissingDataError()
        agency_id = request.POST.get("agency_id")
        account_id = request.POST.get("account_id")

        if agency_id is None and account_id is None:
            raise exc.ValidationError(
                errors={
                    "account_id": ["One of either account or agency must be set."],
                    "agency_id": ["One of either account or agency must be set."],
                }
            )

        account = helpers.get_account(request.user, account_id) if account_id is not None else None
        agency = helpers.get_agency(request.user, agency_id) if agency_id is not None else None

        form = forms.PublisherGroupUploadForm(request.POST, request.FILES, user=request.user)
        if not form.is_valid():
            raise exc.ValidationError(errors=form.errors)

        entries = form.cleaned_data.get("entries")
        if entries:
            include_placement = request.user.has_perm("zemauth.can_use_placement_targeting")

            validated_entries = core.features.publisher_groups.validate_entries(
                entries, include_placement=include_placement
            )
            if any("error" in entry for entry in validated_entries):
                errors_csv_key = core.features.publisher_groups.save_entries_errors_csv(
                    validated_entries, include_placement=include_placement, agency=agency, account=account
                )
                raise exc.ValidationError(errors={"errors_csv_key": errors_csv_key})

            core.features.publisher_groups.clean_entry_sources(entries)

        publisher_group = core.features.publisher_groups.upsert_publisher_group(request, form.cleaned_data, entries)

        return self.create_api_response(serialize_publisher_group(publisher_group))


class PublisherGroupsDownload(api_common.BaseApiView):
    def get(self, request, publisher_group_id):
        if not request.user.has_perm("zemauth.can_edit_publisher_groups"):
            raise exc.MissingDataError()

        try:
            publisher_group = core.features.publisher_groups.PublisherGroup.objects.get(id=int(publisher_group_id))

            if publisher_group.agency is not None:
                try:
                    helpers.get_agency(request.user, publisher_group.agency.id)
                except exc.MissingDataError:
                    accounts = core.models.Account.objects.filter(agency_id=publisher_group.agency.id).filter_by_user(
                        request.user
                    )
                    if accounts.count() < 1:
                        raise exc.MissingDataError("Publisher group does not exist")

            elif publisher_group.account is not None:
                helpers.get_account(request.user, publisher_group.account.id)
            else:
                raise exc.MissingDataError("Publisher group does not exist")

        except core.features.publisher_groups.PublisherGroup.DoesNotExist:
            raise exc.MissingDataError("Publisher group does not exist")

        include_placement = request.user.has_perm("zemauth.can_use_placement_targeting")
        return self.create_csv_response(
            "publisher_group_{}".format(slugify.slugify(publisher_group.name)),
            content=core.features.publisher_groups.get_csv_content(
                publisher_group.entries.all().select_related("source"),
                include_placement=include_placement,
                agency=publisher_group.agency,
                account=publisher_group.account,
            ),
        )


class PublisherGroupsExampleDownload(api_common.BaseApiView):
    def get(self, request):
        if not request.user.has_perm("zemauth.can_edit_publisher_groups"):
            raise exc.MissingDataError()

        include_placement = request.user.has_perm("zemauth.can_use_placement_targeting")
        return self.create_csv_response(
            "publisher_group_example",
            content=core.features.publisher_groups.get_example_csv_content(include_placement=include_placement),
        )
