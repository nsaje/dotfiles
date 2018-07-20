import json
import os

import slugify
from django.conf import settings
from django.db.models import Count

from dash import constants
from dash import forms
from dash import publisher_helpers
from core.publisher_groups import publisher_group_helpers, publisher_group_csv_helpers
from dash import models
from dash import cpc_constraints
from dash.views import helpers
import redshiftapi.api_breakdowns
from utils import api_common
from utils import exc
from utils import s3helpers


def serialize_publisher_group(publisher_group):
    type_, level, obj, obj_name = publisher_group_helpers.parse_default_publisher_group_origin(publisher_group)
    if hasattr(publisher_group, "num_entries"):
        entries_count = publisher_group.num_entries
    else:
        entries_count = publisher_group.entries.all().count()
    return {
        "id": publisher_group.id,
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
        if not publisher_group_helpers.can_user_handle_publisher_listing_level(request.user, obj):
            raise exc.AuthorizationError()

        entry_dicts = form.cleaned_data["entries"]

        if form.cleaned_data["select_all"]:
            entry_dicts = self.get_bulk_selection(form.cleaned_data)

        if entry_dicts:
            try:
                publisher_group_helpers.handle_publishers(
                    request, entry_dicts, obj, form.cleaned_data["status"], enforce_cpc=form.cleaned_data["enforce_cpc"]
                )
            except cpc_constraints.CpcValidationError as e:
                raise exc.ValidationError(errors={"cpc_constraints": list(e)})

        response = {"success": True}
        return self.create_api_response(response)

    def get_bulk_selection(self, obj, cleaned_data):

        constraints = {
            "date__gte": cleaned_data["start_date"],
            "date__lte": cleaned_data["end_date"],
            "source_id": list(cleaned_data["filtered_sources"].values_list("pk", flat=True).order_by("pk")),
        }

        if isinstance(obj, models.AdGroup):
            constraints["ad_group_id"] = obj.pk
        elif isinstance(obj, models.Campaign):
            constraints["campaign_id"] = obj.pk
        elif isinstance(obj, models.Account):
            constraints["account_id"] = obj.pk
        else:
            raise Exception("You probably don't want to blacklist all publishers globaly")

        entries_not_selected = cleaned_data["entries_not_selected"]
        if entries_not_selected:
            constraints["publisher_id__neq"] = [
                publisher_helpers.create_publisher_id(x["publisher"], x["source"].pk if x.get("source") else None)
                for x in entries_not_selected
            ]

        publishers = redshiftapi.api_breakdowns.query_structure_with_stats(
            ["publisher_id"], constraints, use_publishers_view=True
        )

        sources = {x.pk: x for x in models.Source.objects.all()}
        entry_dicts = []
        for publisher_id in publishers:
            publisher, source_id = publisher_helpers.dissect_publisher_id(publisher_id)
            entry_dicts.append(
                {
                    "publisher": publisher,
                    "source": sources[source_id] if source_id else None,
                    "include_subdomains": cleaned_data["status"] == constants.PublisherTargetingStatus.BLACKLISTED,
                }
            )
        return entry_dicts


class PublisherGroups(api_common.BaseApiView):
    def get(self, request, account_id):
        if not request.user.has_perm("zemauth.can_edit_publisher_groups"):
            raise exc.MissingDataError()

        account = helpers.get_account(request.user, account_id)

        publisher_groups_q = (
            models.PublisherGroup.objects.all().filter_by_account(account).annotate(num_entries=Count("entries"))
        )
        if request.GET.get("not_implicit"):
            publisher_groups_q = publisher_groups_q.filter(implicit=False)

        publisher_groups = []
        for pg in publisher_groups_q:
            publisher_groups.append(serialize_publisher_group(pg))

        return self.create_api_response({"publisher_groups": publisher_groups, "success": True})


class PublisherGroupsUpload(api_common.BaseApiView):
    def get(self, request, account_id, csv_key):
        # download errors csv
        if not request.user.has_perm("zemauth.can_edit_publisher_groups"):
            raise exc.MissingDataError()

        account = helpers.get_account(request.user, account_id)

        s3_helper = s3helpers.S3Helper(settings.S3_BUCKET_PUBLISHER_GROUPS)
        content = s3_helper.get(
            os.path.join("publisher_group_errors", "account_{}".format(account.id), csv_key + ".csv")
        )

        return self.create_csv_response("publisher_group_errors", content=content)

    def post(self, request, account_id):
        if not request.user.has_perm("zemauth.can_edit_publisher_groups"):
            raise exc.MissingDataError()

        account = helpers.get_account(request.user, account_id)

        form = forms.PublisherGroupUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            raise exc.ValidationError(errors=form.errors)

        entries = form.cleaned_data.get("entries")
        if entries:
            validated_entries = publisher_group_csv_helpers.validate_entries(entries)
            if any("error" in entry for entry in validated_entries):
                errors_csv_key = publisher_group_csv_helpers.save_entries_errors_csv(account, validated_entries)
                raise exc.ValidationError(errors={"errors_csv_key": errors_csv_key})

            publisher_group_csv_helpers.clean_entry_sources(entries)

        publisher_group = publisher_group_helpers.upsert_publisher_group(
            request, account_id, form.cleaned_data, entries
        )

        return self.create_api_response(serialize_publisher_group(publisher_group))


class PublisherGroupsDownload(api_common.BaseApiView):
    def get(self, request, account_id, publisher_group_id):
        if not request.user.has_perm("zemauth.can_edit_publisher_groups"):
            raise exc.MissingDataError()

        account = helpers.get_account(request.user, account_id)
        publisher_group = helpers.get_publisher_group(request.user, account_id, publisher_group_id)
        if not publisher_group:
            raise exc.MissingDataError()

        return self.create_csv_response(
            "publisher_group_{}".format(slugify.slugify(publisher_group.name)),
            content=publisher_group_csv_helpers.get_csv_content(
                account, publisher_group.entries.all().select_related("source")
            ),
        )


class PublisherGroupsExampleDownload(api_common.BaseApiView):
    def get(self, request):
        if not request.user.has_perm("zemauth.can_edit_publisher_groups"):
            raise exc.MissingDataError()

        return self.create_csv_response(
            "publisher_group_example", content=publisher_group_csv_helpers.get_example_csv_content()
        )
