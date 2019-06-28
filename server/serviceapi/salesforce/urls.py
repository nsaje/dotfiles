from django.conf.urls import url

from . import views

urlpatterns = [
    # Zemanta SalesForce
    url(r"^salesforce/client/$", views.CreateClientView.as_view(), name="service.salesforce.client"),
    url(r"^salesforce/credit/$", views.CreateCreditLineView.as_view(), name="service.salesforce.credit"),
    url(
        r"^salesforce/agency-accounts/$", views.AgencyAccountsView.as_view(), name="service.salesforce.agency_accounts"
    ),
    url(r"^salesforce/credits-list/$", views.CreditsListView.as_view(), name="service.salesforce.credits_list"),
    # OB SalesForce
    url(r"^salesforce/agency/$", views.AgencyView.as_view(), name="service.salesforce.agency"),
    url(r"^salesforce/agency/(?P<agency_id>\d+)$", views.AgencyView.as_view(), name="service.salesforce.agency"),
    url(r"^salesforce/agencies/$", views.AgenciesView.as_view(), name="service.salesforce.agencies"),
    url(r"^salesforce/account/$", views.AccountView.as_view(), name="service.salesforce.account"),
    url(r"^salesforce/account/(?P<account_id>\d+)$", views.AccountView.as_view(), name="service.salesforce.account"),
    url(r"^salesforce/accounts/$", views.AccountsView.as_view(), name="service.salesforce.accounts"),
    url(
        r"^salesforce/account/(?P<account_id>\d+)/archive$",
        views.AccountArchiveView.as_view(),
        name="service.salesforce.account.archive",
    ),
]
