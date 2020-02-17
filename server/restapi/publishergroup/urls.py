from django.conf.urls import include
from django.conf.urls import url

import restapi.publishergroup.internal.urls
import restapi.publishergroup.v1.urls

urlpatterns = [
    url(r"^v1/", include(restapi.publishergroup.v1.urls, namespace="restapi.publishergroup.v1")),
    url(r"^internal/", include(restapi.publishergroup.internal.urls, namespace="restapi.publishergroup.internal")),
]
