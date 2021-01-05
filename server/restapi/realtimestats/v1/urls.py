from django.conf.urls import url

from . import views

app_name = "restapi.realtimestats"
urlpatterns = [
    url(r"realtimestats/$", views.RealtimeStatsViewSet.as_view({"get": "groupby"}), name="groupby"),
    url(r"realtimestats/top/$", views.RealtimeStatsViewSet.as_view({"get": "topn"}), name="topn"),
]
