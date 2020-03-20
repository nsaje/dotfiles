from django.conf.urls import include
from django.conf.urls import url

import restapi.credit.internal.urls
import restapi.credit.v1.urls

urlpatterns = [
    url(r"^v1/", include(restapi.credit.v1.urls, namespace="restapi.credit.v1")),
    url(r"^internal/", include(restapi.credit.internal.urls, namespace="restapi.credit.internal")),
]
