import codecs
import csv
import os

from django.conf import settings
from django.http import HttpResponse
from rest_framework import permissions
from rest_framework import serializers
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

import restapi
from core.features import bid_modifiers
from core.features import publisher_bid_modifiers
from utils import csv_utils
from utils import s3helpers


class CSVMixin(object):
    def _create_file_response(self, content_type, filename, status_code=200, content=""):
        response = HttpResponse(content, content_type=content_type, status=status_code)
        response["Content-Disposition"] = 'attachment; filename="%s"' % filename

        return response

    def create_csv_response(self, filename, status_code=200, content=""):
        return self._create_file_response(
            'text/csv; name="%s.csv"' % filename, "%s.csv" % filename, status_code, content
        )


class PublisherBidModifiersDownload(restapi.common.views_base.RESTAPIBaseViewSet, CSVMixin):
    permission_classes = (permissions.IsAuthenticated,)

    def download(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)

        modifiers = bid_modifiers.BidModifier.publisher_objects.filter(ad_group=ad_group)
        modifiers = [(x.target, x.source.get_clean_slug(), x.modifier) for x in modifiers]
        modifiers.insert(0, ("Publisher", "Source Slug", "Bid Modifier"))

        csv_content = csv_utils.tuplelist_to_csv(modifiers)

        return self.create_csv_response("export", content=csv_content)


class PublisherBidModifiersUpload(restapi.common.views_base.RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser,)

    def upload(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)

        csv_file = codecs.iterdecode(request.data["file"], "utf-8")
        csv_reader = csv.DictReader(csv_file)

        if csv_reader.fieldnames is None:
            raise serializers.ValidationError({"file": "The file is not a proper CSV file!"})

        if "Publisher" not in csv_reader.fieldnames:
            raise serializers.ValidationError({"file": "Publisher column missing in CSV file!"})

        if "Source Slug" not in csv_reader.fieldnames:
            raise serializers.ValidationError({"file": "Source Slug column missing in CSV file!"})

        if "Bid Modifier" not in csv_reader.fieldnames:
            raise serializers.ValidationError({"file": "Bid Modifier column missing in CSV file!"})

        error_csv_columns = csv_reader.fieldnames + ["Errors"]

        entries = list(csv_reader)
        cleaned_entries, error = publisher_bid_modifiers.service.clean_entries(entries)

        if error:
            csv_error_key = publisher_bid_modifiers.service.make_csv_error_file(entries, error_csv_columns, ad_group.id)

            raise serializers.ValidationError({"file": "Errors in CSV file!", "errorFileUrl": csv_error_key})
        else:
            for entry in cleaned_entries:
                publisher_bid_modifiers.set(ad_group, entry["publisher"], entry["source"], entry["modifier"])

            return Response({}, status=200)


class PublisherBidModifiersErrorDownload(restapi.common.views_base.RESTAPIBaseViewSet, CSVMixin):
    permission_classes = (permissions.IsAuthenticated,)

    def download(self, request, ad_group_id, csv_error_key):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)

        s3_helper = s3helpers.S3Helper(settings.S3_BUCKET_PUBLISHER_GROUPS)
        content = s3_helper.get(
            os.path.join("publisher_bid_modifier_errors", "ad_group_{}".format(ad_group.id), csv_error_key + ".csv")
        )

        return self.create_csv_response("publisher_bid_modifier_errors", content=content)


class PublisherBidModifiersExampleCSVDownload(restapi.common.views_base.RESTAPIBaseViewSet, CSVMixin):
    permission_classes = (permissions.IsAuthenticated,)

    def download(self, request):
        csv_example_file = publisher_bid_modifiers.service.make_csv_example_file()
        return self.create_csv_response("example_bid_modifiers", content=csv_example_file)
