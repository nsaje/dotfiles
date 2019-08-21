from django.conf.urls import url

from . import views

app_name = "restapi.conversion_pixel"
urlpatterns = [
    url(
        r"^(?P<account_id>\d+)/pixels/(?P<pixel_id>\d+)$",
        views.ConversionPixelViewSet.as_view({"get": "get", "put": "put"}),
        name="pixels_details",
    ),
    url(
        r"^(?P<account_id>\d+)/pixels/$",
        views.ConversionPixelViewSet.as_view({"get": "list", "post": "create"}),
        name="pixels_list",
    ),
]
