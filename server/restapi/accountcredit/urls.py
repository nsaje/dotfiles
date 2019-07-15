from django.conf.urls import include
from django.conf.urls import url

import restapi.accountcredit.internal.urls
import restapi.accountcredit.v1.urls

urlpatterns = [
    url(r"^v1/accounts/", include(restapi.accountcredit.v1.urls, namespace="restapi.accountcredit.v1")),
    url(
        r"^internal/accounts/", include(restapi.accountcredit.internal.urls, namespace="restapi.accountcredit.internal")
    ),
]
