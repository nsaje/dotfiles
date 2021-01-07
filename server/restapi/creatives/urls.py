from django.conf.urls import include
from django.conf.urls import url

import restapi.creatives.internal.urls

urlpatterns = [
    url(r"^internal/creatives/", include(restapi.creatives.internal.urls, namespace="restapi.creatives.internal"))
]
