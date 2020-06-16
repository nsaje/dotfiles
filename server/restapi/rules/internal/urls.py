from django.conf.urls import url

from . import views

app_name = "restapi.rules"
urlpatterns = [
    url(r"^(?P<rule_id>\d+)$", views.RuleViewSet.as_view({"get": "get", "put": "put"}), name="rules_details"),
    url(r"^$", views.RuleViewSet.as_view({"get": "list", "post": "create"}), name="rules_list"),
    url(r"^history/$", views.RuleHistoryViewSet.as_view({"get": "list"}), name="rules_history"),
]
