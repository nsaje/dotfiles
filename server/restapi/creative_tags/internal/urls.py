from django.conf.urls import url

from . import views

app_name = "restapi.creative_tags"
urlpatterns = [url(r"^$", views.CreativeTagViewSet.as_view({"get": "list"}), name="creative_tag_list")]
