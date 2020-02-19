from django.conf.urls import include
from django.conf.urls import url

import restapi.availablesources.internal.urls

urlpatterns = [
    url(r"^internal/agencies/", include(restapi.availablesources.internal.urls, namespace="restapi.source.internal"))
]
