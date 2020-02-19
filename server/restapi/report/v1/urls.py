from django.conf.urls import url

from restapi.report.v1 import views

app_name = "restapi.report"
urlpatterns = [
    url(r"^(?P<job_id>\d+)$", views.ReportsViewSet.as_view({"get": "get"}), name="reports_details"),
    url(r"^$", views.ReportsViewSetCreate.as_view({"post": "create"}), name="reports_list"),
]
