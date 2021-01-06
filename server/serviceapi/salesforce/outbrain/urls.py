from django.conf.urls import url

from . import views

urlpatterns = [
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
    url(r"^salesforce/user/$", views.UserView.as_view(), name="service.salesforce.user"),
    url(r"^salesforce/user/(?P<user_id>\d+)$", views.UserView.as_view(), name="service.salesforce.user"),
    url(r"^salesforce/users/$", views.UsersView.as_view(), name="service.salesforce.users"),
]
