from django.conf.urls import url

from core.features.bid_modifiers import helpers

from . import views

allowed_types = "|".join(helpers.supported_breakdown_names())

urlpatterns = [
    url(
        r"^adgroups/(?P<ad_group_id>\d+)/bidmodifiers/download/$",
        views.BidModifiersDownload.as_view({"get": "download"}),
        name="bid_modifiers_download_bulk",
    ),
    url(
        r"^adgroups/(?P<ad_group_id>\d+)/bidmodifiers/download/(?P<breakdown_name>(" + allowed_types + r")+)/$",
        views.BidModifiersDownload.as_view({"get": "download"}),
        name="bid_modifiers_download",
    ),
    url(
        r"^adgroups/(?P<ad_group_id>\d+)/bidmodifiers/validate/$",
        views.BidModifiersUpload.as_view({"post": "validate"}),
        name="bid_modifiers_validate_bulk",
    ),
    url(
        r"^adgroups/(?P<ad_group_id>\d+)/bidmodifiers/validate/(?P<breakdown_name>(" + allowed_types + r")+)/$",
        views.BidModifiersUpload.as_view({"post": "validate"}),
        name="bid_modifiers_validate",
    ),
    url(
        r"^adgroups/(?P<ad_group_id>\d+)/bidmodifiers/upload/$",
        views.BidModifiersUpload.as_view({"post": "upload"}),
        name="bid_modifiers_upload_bulk",
    ),
    url(
        r"^adgroups/(?P<ad_group_id>\d+)/bidmodifiers/upload/(?P<breakdown_name>(" + allowed_types + r")+)/$",
        views.BidModifiersUpload.as_view({"post": "upload"}),
        name="bid_modifiers_upload",
    ),
    url(
        r"^adgroups/(?P<ad_group_id>\d+)/bidmodifiers/error_download/(?P<csv_error_key>[a-zA-Z0-9]+)/$",
        views.BidModifiersErrorDownload.as_view({"get": "download"}),
        name="bid_modifiers_error_download",
    ),
    url(
        r"^adgroups/bidmodifiers/error_download/(?P<csv_error_key>[a-zA-Z0-9]+)/$",
        views.BidModifiersErrorDownload.as_view({"get": "download_new"}),
        name="bid_modifiers_error_download_new",
    ),
    url(
        r"^adgroups/bidmodifiers/example_csv_download/$",
        views.BidModifiersExampleCSVDownload.as_view({"get": "download"}),
        name="bid_modifiers_example_download_bulk",
    ),
    url(
        r"^adgroups/bidmodifiers/example_csv_download/(?P<breakdown_name>(" + allowed_types + r")+)/$",
        views.BidModifiersExampleCSVDownload.as_view({"get": "download"}),
        name="bid_modifiers_example_download",
    ),
    url(
        r"^adgroups/(?P<ad_group_id>\d+)/bidmodifiers/type_summaries/$",
        views.BidModifierTypeSummariesViewSet.as_view({"get": "retrieve"}),
        name="bid_modifiers_type_summaries",
    ),
    url(
        r"^adgroups/bidmodifiers/validate/(?P<breakdown_name>(" + allowed_types + r")+)/$",
        views.BidModifiersUpload.as_view({"post": "validate_new"}),
        name="bid_modifiers_validate_new",
    ),
    url(
        r"^adgroups/bidmodifiers/validate/$",
        views.BidModifiersUpload.as_view({"post": "validate_new"}),
        name="bid_modifiers_validate_bulk_new",
    ),
]
