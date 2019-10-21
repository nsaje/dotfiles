import structlog
from rest_framework import exceptions
from rest_framework import permissions
from rest_framework import serializers
from rest_framework import throttling

import restapi.throttling
from dash.features.reports import reportjob
from dash.features.reports import reports
from dash.features.reports import serializers as reports_serializers
from restapi.common.views_base import RESTAPIBaseViewSet

logger = structlog.get_logger(__name__)


class ReportsViewSet(RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, job_id):
        job = reportjob.ReportJob.objects.get(pk=job_id)
        if job.user != request.user:
            raise exceptions.PermissionDenied
        return self.response_ok(reports_serializers.ReportJobSerializer(job).data)


class ReportsViewSetCreate(RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = (restapi.throttling.UserRateOverrideThrottle, throttling.ScopedRateThrottle)
    throttle_scope = "reportjob-create"

    def create(self, request):
        query = reports_serializers.ReportQuerySerializer(data=request.data, context={"request": request})
        try:
            query.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            logger.debug(e)
            raise e

        job = reports.create_job(request.user, query.data)

        return self.response_ok(reports_serializers.ReportJobSerializer(job).data, status=201)
