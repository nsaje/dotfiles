from django.conf.urls import include
from django.conf.urls import url

import restapi.account.internal.urls
import restapi.account.v1.urls

urlpatterns = [
    url(r"^v1/accounts/", include(restapi.account.v1.urls, namespace="restapi.account.v1")),
    url(r"^internal/accounts/", include(restapi.account.internal.urls, namespace="restapi.account.internal")),
]
