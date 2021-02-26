from django.conf.urls import url

from restapi.entityhistory.internal import views

app_name = "restapi.entityhistory"
urlpatterns = [
    url(r"^entityhistory/$", views.EntityHistoryViewSet.as_view({"get": "list"}), name="entity_history_details"),
]
