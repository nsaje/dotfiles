from django.conf.urls import url

import views.video_upload_callback
import views.salesforce

urlpatterns = [
    url(
        r'^videoassets/(?P<videoasset_id>.+)$',
        views.video_upload_callback.VideoUploadCallbackView.as_view(),
        name='service.videoassets'
    ),

    url(
        r'^salesforce/client/$',
        views.salesforce.CreateClientView.as_view(),
        name='service.salesforce.client'
    ),
    url(
        r'^salesforce/credit/$',
        views.salesforce.CreateCreditLineView.as_view(),
        name='service.salesforce.credit'
    ),
    url(
        r'^salesforce/agency-accounts/$',
        views.salesforce.AgencyAccountsView.as_view(),
        name='service.salesforce.agency_accounts'
    ),
]
