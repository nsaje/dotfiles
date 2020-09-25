import json
import os

import slugify
from django.conf import settings
from django.db.models import Q

import core.features.publisher_groups
import zemauth.access
from dash import forms
from dash import models
from dash.common.views_base import DASHAPIBaseView
from utils import exc
from utils import s3helpers
from zemauth.features.entity_permission import Permission


def serialize_publisher_group(publisher_group):
    type_, level, obj, obj_name = core.features.publisher_groups.parse_default_publisher_group_origin(publisher_group)

    return {
        "id": publisher_group.id,
        "agency_id": str(publisher_group.agency.id) if publisher_group.agency else None,
        "agency_name": str(publisher_group.agency.name) if publisher_group.agency else None,
        "account_id": str(publisher_group.account.id) if publisher_group.account else None,
        "account_name": str(publisher_group.account.settings.name) if publisher_group.account else None,
        "name": publisher_group.name,
        "include_subdomains": publisher_group.default_include_subdomains,
        "implicit": publisher_group.implicit,
        "size": publisher_group.entities_count if publisher_group.entities_count else None,
        "modified": publisher_group.modified_dt,
        "created": publisher_group.created_dt,
        "type": type_,
        "level": level,
        "level_name": obj_name,
        "level_id": obj.id if obj else None,
    }


class PublisherTargeting(DASHAPIBaseView):
    def post(self, request):
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


class PublisherGroups(DASHAPIBaseView):
    def get(self, request):
        agency_id = request.GET.get("agency_id")
        account_id = request.GET.get("account_id")

        if account_id is not None:
            account = zemauth.access.get_account(request.user, Permission.READ, account_id)
            publisher_groups_q = models.PublisherGroup.objects.filter_by_account(account).annotate_entities_count()
        elif agency_id is not None:
            agency = zemauth.access.get_agency(request.user, Permission.READ, agency_id)
            publisher_groups_q = models.PublisherGroup.objects.filter(
                Q(agency=agency) | Q(account__agency=agency)
            ).annotate_entities_count()
        else:
            raise exc.ValidationError(errors={"non_field_errors": "Either agency id or account id must be provided."})

        if request.GET.get("not_implicit"):
            publisher_groups_q = publisher_groups_q.filter(implicit=False)

        publisher_groups = []
        for pg in publisher_groups_q:
            publisher_groups.append(serialize_publisher_group(pg))

        return self.create_api_response({"publisher_groups": publisher_groups, "success": True})


class PublisherGroupsUpload(DASHAPIBaseView):
    def get(self, request, csv_key):
        # download errors csv
        agency_id = request.GET.get("agency_id")
        account_id = request.GET.get("account_id")

        if agency_id is None and account_id is None:
            raise exc.ValidationError(
                errors={
                    "account_id": ["One of either account or agency must be set."],
                    "agency_id": ["One of either account or agency must be set."],
                }
            )

        account = (
            zemauth.access.get_account(request.user, Permission.READ, account_id) if account_id is not None else None
        )
        agency = zemauth.access.get_agency(request.user, Permission.READ, agency_id) if agency_id is not None else None

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
        agency_id = request.POST.get("agency_id")
        account_id = request.POST.get("account_id")

        if agency_id is None and account_id is None:
            raise exc.ValidationError(
                errors={
                    "account_id": ["One of either account or agency must be set."],
                    "agency_id": ["One of either account or agency must be set."],
                }
            )

        account = (
            zemauth.access.get_account(request.user, Permission.WRITE, account_id) if account_id is not None else None
        )
        agency = zemauth.access.get_agency(request.user, Permission.WRITE, agency_id) if agency_id is not None else None

        form = forms.PublisherGroupUploadForm(request.POST, request.FILES, user=request.user)
        if not form.is_valid():
            raise exc.ValidationError(errors=form.errors)

        entries = form.cleaned_data.get("entries")
        entities_count = 0
        if entries:
            validated_entries = core.features.publisher_groups.validate_entries(entries)
            if any("error" in entry for entry in validated_entries):
                errors_csv_key = core.features.publisher_groups.save_entries_errors_csv(
                    validated_entries, agency=agency, account=account
                )
                raise exc.ValidationError(errors={"errors_csv_key": errors_csv_key})

            core.features.publisher_groups.clean_entry_sources(entries)
            entities_count = len(validated_entries)

        publisher_group = core.features.publisher_groups.upsert_publisher_group(request, form.cleaned_data, entries)
        publisher_group.entities_count = entities_count

        return self.create_api_response(serialize_publisher_group(publisher_group))


class PublisherGroupsDownload(DASHAPIBaseView):
    def get(self, request, publisher_group_id):
        try:
            publisher_group = core.features.publisher_groups.PublisherGroup.objects.get(id=int(publisher_group_id))

            if publisher_group.agency is not None:
                try:
                    zemauth.access.get_agency(request.user, Permission.READ, publisher_group.agency.id)
                except exc.MissingDataError:
                    accounts = core.models.Account.objects.filter(
                        agency_id=publisher_group.agency.id
                    ).filter_by_entity_permission(request.user, Permission.READ)
                    if accounts.count() < 1:
                        raise exc.MissingDataError("Publisher group does not exist")

            elif publisher_group.account is not None:
                zemauth.access.get_account(request.user, Permission.READ, publisher_group.account.id)
            else:
                raise exc.MissingDataError("Publisher group does not exist")

        except core.features.publisher_groups.PublisherGroup.DoesNotExist:
            raise exc.MissingDataError("Publisher group does not exist")

        return self.create_csv_response(
            "publisher_group_{}".format(slugify.slugify(publisher_group.name)),
            content=core.features.publisher_groups.get_csv_content(
                publisher_group.entries.all().select_related("source"),
                agency=publisher_group.agency,
                account=publisher_group.account,
            ),
        )


class PublisherGroupsExampleDownload(DASHAPIBaseView):
    def get(self, request):
        return self.create_csv_response(
            "publisher_group_example", content=core.features.publisher_groups.get_example_csv_content()
        )
