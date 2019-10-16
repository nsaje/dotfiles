# -*- coding: utf-8 -*-

import mimetypes

from django.conf import settings

import structlog
from utils import api_common
from utils import exc
from utils import s3helpers

logger = structlog.get_logger(__name__)


class ExportApiView(api_common.BaseApiView):
    def dispatch(self, request, *args, **kwargs):
        try:
            return super(api_common.BaseApiView, self).dispatch(request, *args, **kwargs)
        except Exception as e:
            return self.get_exception_response(request, e)


class CustomReportDownload(ExportApiView):
    def get(self, request):
        if not request.user.has_perm("zemauth.can_download_custom_reports"):
            raise exc.MissingDataError()

        path = request.GET.get("path")
        if not path:
            raise exc.ValidationError("Path not specified.")
        filename = path.split("/")[-1]
        s3 = s3helpers.S3Helper(settings.S3_BUCKET_CUSTOM_REPORTS)
        try:
            content = s3.get(path)
        except Exception:
            logger.exception("Failed to fetch {} from s3.".format(path))
            raise exc.MissingDataError()
        mime, encoding = mimetypes.guess_type(filename)
        return self.create_file_response(
            '{}; name="{}"'.format(mime or "text/csv", filename), filename, content=content
        )
