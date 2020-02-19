from django.conf.urls import include
from django.conf.urls import url

import restapi.accountcreditrefund.internal.urls

urlpatterns = [
    url(
        r"^internal/accounts/",
        include(restapi.accountcreditrefund.internal.urls, namespace="restapi.accountcreditrefund.internal"),
    )
]
