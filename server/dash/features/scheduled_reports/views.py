import json

import zemauth.access
from dash.common.views_base import DASHAPIBaseView
from utils import exc
from zemauth.features.entity_permission import Permission

from . import models
from . import serializers


class ScheduledReports(DASHAPIBaseView):
    def get(self, request):
        account = None
        account_id = request.GET.get("account_id")
        if account_id:
            account = zemauth.access.get_account(request.user, Permission.READ, account_id)

        scheduled_reports = models.ScheduledReport.objects.for_view(request.user, account)

        serializer = serializers.ScheduledReportSerializer(scheduled_reports, many=True)

        return self.create_api_response({"reports": serializer.data})

    def put(self, request):
        try:
            data = json.loads(request.body)
        except ValueError:
            raise exc.ValidationError(message="Invalid json")

        serializer = serializers.ScheduledReportSerializer(data=data, context={"request": request})
        if not serializer.is_valid(raise_exception=False):
            raise exc.ValidationError(errors=serializer.errors)

        models.ScheduledReport.objects.create(user=request.user, **serializer.validated_data)

        return self.create_api_response(None)


class ScheduledReportsDelete(DASHAPIBaseView):
    def delete(self, request, scheduled_report_id):
        scheduled_report = models.ScheduledReport.objects.get(id=scheduled_report_id)

        if scheduled_report.user != request.user:
            raise exc.ForbiddenError(message="Not allowed")

        scheduled_report.remove()

        return self.create_api_response({})
