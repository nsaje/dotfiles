from django.conf.urls import url

from . import views

app_name = "restapi.bluekai"
urlpatterns = [
    url(r"^taxonomy/$", views.TaxonomyTreeInternalViewSet.as_view({"get": "get"}), name="bluekai_taxonomy"),
    url(r"^reach/$", views.SegmentReachViewSet.as_view({"post": "post"}), name="bluekai_reach"),
]
