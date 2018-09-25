import csv
import codecs
import os

from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from django.http import HttpResponse
from django.conf import settings

from core.publisher_bid_modifiers import PublisherBidModifier, service
from core import publisher_bid_modifiers
from rest_framework import serializers
from utils import csv_utils
from utils import s3helpers
import restapi


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
    def download(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)

        modifiers = PublisherBidModifier.objects.filter(ad_group=ad_group)
        modifiers = [(x.publisher, x.source.get_clean_slug(), x.modifier) for x in modifiers]
        modifiers.insert(0, ("Publisher", "Source Slug", "Bid Modifier"))

        csv_content = csv_utils.tuplelist_to_csv(modifiers)

        return self.create_csv_response("export", content=csv_content)


class PublisherBidModifiersUpload(restapi.common.views_base.RESTAPIBaseViewSet):

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
        cleaned_entries, error = service.clean_entries(entries)

        if error:
            csv_error_key = service.make_csv_error_file(entries, error_csv_columns, ad_group.id)

            raise serializers.ValidationError({"file": "Errors in CSV file!", "errorFileUrl": csv_error_key})
        else:
            for entry in cleaned_entries:
                publisher_bid_modifiers.set(ad_group, entry["publisher"], entry["source"], entry["modifier"])

            return Response({}, status=200)


class PublisherBidModifiersErrorDownload(restapi.common.views_base.RESTAPIBaseViewSet, CSVMixin):
    def download(self, request, ad_group_id, csv_error_key):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)

        s3_helper = s3helpers.S3Helper(settings.S3_BUCKET_PUBLISHER_GROUPS)
        content = s3_helper.get(
            os.path.join("publisher_bid_modifier_errors", "ad_group_{}".format(ad_group.id), csv_error_key + ".csv")
        )

        return self.create_csv_response("publisher_bid_modifier_errors", content=content)
