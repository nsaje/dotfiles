from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^salesforce/client/$", views.CreateClientView.as_view(), name="service.salesforce.client"),
    url(r"^salesforce/credit/$", views.CreateCreditLineView.as_view(), name="service.salesforce.credit"),
    url(
        r"^salesforce/agency-accounts/$", views.AgencyAccountsView.as_view(), name="service.salesforce.agency_accounts"
    ),
    url(r"^salesforce/credits-list/$", views.CreditsListView.as_view(), name="service.salesforce.credits_list"),
]
