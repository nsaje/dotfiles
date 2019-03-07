from django.conf.urls import url

from core.features.bid_modifiers import constants

from . import views

allowed_types = "|".join(constants.BidModifierType.get_all_names())

urlpatterns = [
    url(
        r"^internal/adgroups/(?P<ad_group_id>\d+)/bidmodifiers/download/$",
        views.BidModifiersDownload.as_view({"get": "download"}),
        name="bid_modifiers_download_bulk",
    ),
    url(
        r"^internal/adgroups/(?P<ad_group_id>\d+)/bidmodifiers/download/(?P<modifier_type>(" + allowed_types + r")+)/$",
        views.BidModifiersDownload.as_view({"get": "download"}),
        name="bid_modifiers_download",
    ),
    url(
        r"^internal/adgroups/(?P<ad_group_id>\d+)/bidmodifiers/upload/$",
        views.BidModifiersUpload.as_view({"post": "upload"}),
        name="bid_modifiers_upload_bulk",
    ),
    url(
        r"^internal/adgroups/(?P<ad_group_id>\d+)/bidmodifiers/upload/(?P<modifier_type>(" + allowed_types + r")+)/$",
        views.BidModifiersUpload.as_view({"post": "upload"}),
        name="bid_modifiers_upload",
    ),
    url(
        r"^internal/adgroups/(?P<ad_group_id>\d+)/bidmodifiers/error_download/(?P<csv_error_key>[a-zA-Z0-9]+)/$",
        views.BidModifiersErrorDownload.as_view({"get": "download"}),
        name="bid_modifiers_error_download",
    ),
    url(
        r"^internal/adgroups/bidmodifiers/example_csv_download/$",
        views.BidModifiersExampleCSVDownload.as_view({"get": "download"}),
        name="bid_modifiers_example_download_bulk",
    ),
    url(
        r"^internal/adgroups/bidmodifiers/example_csv_download/(?P<modifier_type>(" + allowed_types + r")+)/$",
        views.BidModifiersExampleCSVDownload.as_view({"get": "download"}),
        name="bid_modifiers_example_download",
    ),
]
