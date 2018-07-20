import json

from dash.views import helpers
from utils import api_common
from utils import exc

from . import models
from . import serializers


class ScheduledReports(api_common.BaseApiView):
    def get(self, request):
        account = None
        account_id = request.GET.get("account_id")
        if account_id:
            account = helpers.get_account(request.user, account_id)

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


class ScheduledReportsDelete(api_common.BaseApiView):
    def delete(self, request, scheduled_report_id):
        scheduled_report = models.ScheduledReport.objects.get(id=scheduled_report_id)

        if scheduled_report.user != request.user:
            raise exc.ForbiddenError(message="Not allowed")

        scheduled_report.remove()

        return self.create_api_response({})
