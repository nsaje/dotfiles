from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^v1/reports/(?P<job_id>\d+)$", views.ReportsViewSet.as_view({"get": "get"}), name="reports_details"),
    url(r"^v1/reports/$", views.ReportsViewSet.as_view({"post": "create"}), name="reports_list"),
]
