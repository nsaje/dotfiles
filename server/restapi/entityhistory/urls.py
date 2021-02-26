from django.conf.urls import include
from django.conf.urls import url

import restapi.entityhistory.internal.urls

urlpatterns = [
    url(r"^internal/", include(restapi.entityhistory.internal.urls, namespace="restapi.entityhistory.internal"))
]
