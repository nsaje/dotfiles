from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r"^internal/adgroups/(?P<ad_group_id>\d+)/publishers/modifiers/download/$",
        views.PublisherBidModifiersDownload.as_view({"get": "download"}),
        name="publisher_bid_modifiers_download",
    ),
    url(
        r"^internal/adgroups/(?P<ad_group_id>\d+)/publishers/modifiers/upload/$",
        views.PublisherBidModifiersUpload.as_view({"post": "upload"}),
        name="publisher_bid_modifiers_upload",
    ),
    url(
        r"^internal/adgroups/(?P<ad_group_id>\d+)/publishers/modifiers/error_download/(?P<csv_error_key>[a-zA-Z0-9]+)$",
        views.PublisherBidModifiersErrorDownload.as_view({"get": "download"}),
        name="publisher_bid_modifiers_error_download",
    ),
]
