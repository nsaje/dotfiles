from django.conf.urls import include
from django.conf.urls import url

import restapi.bidmodifiers.internal.urls
import restapi.bidmodifiers.v1.urls

urlpatterns = [
    url(r"^v1/", include(restapi.bidmodifiers.v1.urls)),
    url(r"^internal/", include(restapi.bidmodifiers.internal.urls)),
]
