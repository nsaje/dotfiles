import codecs

from django.conf import settings
from rest_framework import permissions
from rest_framework import serializers
from rest_framework.parsers import MultiPartParser

import core.models
import restapi
from core.features import bid_modifiers
from restapi.common import permissions as restapi_permissions
from utils import csv_utils
from utils import exc as util_exc
from utils import s3helpers


class BidModifiersDownload(restapi.common.views_base.RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated, restapi_permissions.CanSetBidModifiersPermission)

    def download(self, request, ad_group_id, breakdown_name=None):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)

        if breakdown_name:
            modifier_type = bid_modifiers.helpers.breakdown_name_to_modifier_type(breakdown_name)
            cleaned_modifiers = bid_modifiers.service.get(ad_group, include_types=[modifier_type])
            csv_content = bid_modifiers.service.make_csv_file(modifier_type, cleaned_modifiers)
        else:
            cleaned_modifiers = bid_modifiers.service.get(ad_group)
            csv_content = bid_modifiers.service.make_bulk_csv_file(cleaned_modifiers)

        return csv_utils.create_csv_response(data=csv_content, filename="bid_modifiers_export")


class BidModifiersUpload(restapi.common.views_base.RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated, restapi_permissions.CanSetBidModifiersPermission)
    parser_classes = (MultiPartParser,)

    def validate_new(self, request, breakdown_name=None):
        return self._validate(request, ad_group_id=None, breakdown_name=breakdown_name)

    def validate(self, request, ad_group_id, breakdown_name=None):
        _ = restapi.access.get_ad_group(request.user, ad_group_id)
        return self._validate(request, ad_group_id=ad_group_id, breakdown_name=breakdown_name)

    def _validate(self, request, ad_group_id=None, breakdown_name=None):
        csv_file = codecs.iterdecode(request.data["file"], "utf-8")

        try:
            if breakdown_name:
                modifier_type = bid_modifiers.helpers.breakdown_name_to_modifier_type(breakdown_name)

                cleaned_entries, _, csv_error_key = bid_modifiers.service.validate_csv_file_upload(
                    ad_group_id, csv_file, modifier_type=modifier_type
                )

                delete_type_counts = (
                    bid_modifiers.count_types(ad_group_id, [modifier_type], user=request.user)
                    if ad_group_id is not None
                    else {}
                )
            else:
                cleaned_entries, csv_error_key = bid_modifiers.service.validate_bulk_csv_file_upload(
                    ad_group_id, csv_file
                )

                delete_type_counts = (
                    bid_modifiers.count_types(ad_group_id, bid_modifiers.BidModifierType.get_all(), user=request.user)
                    if ad_group_id is not None
                    else {}
                )

            if csv_error_key:
                raise serializers.ValidationError({"file": "Errors in CSV file!", "errorFileUrl": csv_error_key})

        except bid_modifiers.exceptions.InvalidBidModifierFile as exc:
            raise serializers.ValidationError({"file": str(exc)})

        return self.response_ok(
            bid_modifiers.helpers.create_upload_summary_response(
                delete_type_counts, [bid_modifiers.BidModifierData(**e) for e in cleaned_entries]
            )
        )

    def upload(self, request, ad_group_id, breakdown_name=None):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)

        csv_file = codecs.iterdecode(request.data["file"], "utf-8")

        try:
            if breakdown_name:
                modifier_type = bid_modifiers.helpers.breakdown_name_to_modifier_type(breakdown_name)

                number_of_deleted, instances, csv_error_key = bid_modifiers.service.process_csv_file_upload(
                    ad_group, csv_file, modifier_type=modifier_type, user=request.user
                )
                delete_type_counts = [{"type": modifier_type, "count": number_of_deleted}]
            else:
                delete_type_counts = list(
                    bid_modifiers.count_types(ad_group, bid_modifiers.BidModifierType.get_all(), user=request.user)
                )

                number_of_deleted, instances, csv_error_key = bid_modifiers.service.process_bulk_csv_file_upload(
                    ad_group, csv_file, user=request.user
                )

            if csv_error_key:
                raise serializers.ValidationError({"file": "Errors in CSV file!", "errorFileUrl": csv_error_key})

        except bid_modifiers.exceptions.InvalidBidModifierFile as exc:
            raise serializers.ValidationError({"file": str(exc)})

        return self.response_ok(bid_modifiers.helpers.create_upload_summary_response(delete_type_counts, instances))


class BidModifiersErrorDownload(restapi.common.views_base.RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated, restapi_permissions.CanSetBidModifiersPermission)

    def download(self, request, ad_group_id, csv_error_key):
        _ = restapi.access.get_ad_group(request.user, ad_group_id)

        return self._download(request, ad_group_id, csv_error_key)

    def download_new(self, request, csv_error_key):
        return self._download(request, None, csv_error_key)

    def _download(self, request, ad_group_id, csv_error_key):
        s3_helper = s3helpers.S3Helper(settings.S3_BUCKET_PUBLISHER_GROUPS)
        content = s3_helper.get(bid_modifiers.create_error_file_path(ad_group_id, csv_error_key))

        return csv_utils.create_csv_response(data=content, filename="bid_modifiers_errors")


class BidModifiersExampleCSVDownload(restapi.common.views_base.RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated, restapi_permissions.CanSetBidModifiersPermission)

    def download(self, request, breakdown_name=None):
        if breakdown_name:
            modifier_type = bid_modifiers.helpers.breakdown_name_to_modifier_type(breakdown_name)
            csv_example_file = bid_modifiers.service.make_csv_example_file(modifier_type)
        else:
            csv_example_file = bid_modifiers.service.make_bulk_csv_example_file()

        return csv_utils.create_csv_response(data=csv_example_file, filename="example_bid_modifiers")


class BidModifierTypeSummariesViewSet(restapi.common.views_base.RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated, restapi_permissions.CanSetBidModifiersPermission)

    def retrieve(self, request, ad_group_id):
        try:
            ad_group = core.models.AdGroup.objects.filter_by_user(request.user).get(id=ad_group_id)
        except core.models.AdGroup.DoesNotExist:
            raise util_exc.MissingDataError("Ad Group does not exist")

        type_summaries = bid_modifiers.overview.get_type_summaries(ad_group.id)
        return self.response_ok(
            restapi.serializers.bid_modifiers.BidModifierTypeSummary(type_summaries, many=True).data
        )
