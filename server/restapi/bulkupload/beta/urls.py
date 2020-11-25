from django.conf.urls import url

from . import views

app_name = "restapi.bulkupload"
urlpatterns = [
    url(r"^(?P<task_id>.+)$", views.BulkAdGroupsViewSet.as_view({"get": "get"}), name="bulkadgroups_details"),
    url(r"^$", views.BulkAdGroupsViewSet.as_view({"post": "create"}), name="bulkadgroups_list"),
]
