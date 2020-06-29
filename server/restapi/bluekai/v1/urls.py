from django.conf.urls import url

from . import views

app_name = "restapi.bluekai"
urlpatterns = [url(r"^taxonomy/$", views.TaxonomyTreeViewSet.as_view({"get": "get"}), name="bluekai_taxonomy")]
