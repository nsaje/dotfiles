import codecs
import os

from django.conf import settings
from rest_framework import permissions
from rest_framework import serializers
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

import restapi
from core.features import bid_modifiers
from restapi.common import permissions as restapi_permissions
from utils import csv_utils
from utils import s3helpers


class BidModifiersDownload(restapi.common.views_base.RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated, restapi_permissions.CanSetBidModifiersPermission)

    def download(self, request, ad_group_id, breakdown_name=None):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)

        if breakdown_name:
            modifier_type = bid_modifiers.helpers.breakdown_name_modifier_name(breakdown_name)
            cleaned_modifiers = bid_modifiers.service.get(ad_group, include_types=[modifier_type])
            csv_content = bid_modifiers.service.make_csv_file(modifier_type, cleaned_modifiers)
        else:
            cleaned_modifiers = bid_modifiers.service.get(ad_group)
            csv_content = bid_modifiers.service.make_bulk_csv_file(cleaned_modifiers)

        return csv_utils.create_csv_response(data=csv_content, filename="bid_modifiers_export")


class BidModifiersUpload(restapi.common.views_base.RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated, restapi_permissions.CanSetBidModifiersPermission)
    parser_classes = (MultiPartParser,)

    def upload(self, request, ad_group_id, breakdown_name=None):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)

        csv_file = codecs.iterdecode(request.data["file"], "utf-8")

        try:
            if breakdown_name:
                modifier_type = bid_modifiers.helpers.breakdown_name_modifier_name(breakdown_name)
                csv_error_key = bid_modifiers.service.process_csv_file_upload(
                    ad_group, csv_file, modifier_type=modifier_type, user=request.user
                )
            else:
                csv_error_key = bid_modifiers.service.process_bulk_csv_file_upload(
                    ad_group, csv_file, user=request.user
                )

            if csv_error_key:
                raise serializers.ValidationError({"file": "Errors in CSV file!", "errorFileUrl": csv_error_key})

        except bid_modifiers.exceptions.InvalidBidModifierFile as exc:
            raise serializers.ValidationError({"file": str(exc)})

        return Response({}, status=200)


class BidModifiersErrorDownload(restapi.common.views_base.RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated, restapi_permissions.CanSetBidModifiersPermission)

    def download(self, request, ad_group_id, csv_error_key):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)

        s3_helper = s3helpers.S3Helper(settings.S3_BUCKET_PUBLISHER_GROUPS)
        content = s3_helper.get(
            os.path.join("bid_modifier_errors", "ad_group_{}".format(ad_group.id), csv_error_key + ".csv")
        )

        return csv_utils.create_csv_response(data=content, filename="bid_modifiers_errors")


class BidModifiersExampleCSVDownload(restapi.common.views_base.RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated, restapi_permissions.CanSetBidModifiersPermission)

    def download(self, request, breakdown_name=None):
        if breakdown_name:
            modifier_type = bid_modifiers.helpers.breakdown_name_modifier_name(breakdown_name)
            csv_example_file = bid_modifiers.service.make_csv_example_file(modifier_type)
        else:
            csv_example_file = bid_modifiers.service.make_bulk_csv_example_file()

        return csv_utils.create_csv_response(data=csv_example_file, filename="example_bid_modifiers")
