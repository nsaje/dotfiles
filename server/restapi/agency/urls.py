from django.conf.urls import include
from django.conf.urls import url

import restapi.agency.internal.urls

urlpatterns = [url(r"^internal/agencies/", include(restapi.agency.internal.urls, namespace="restapi.agency.internal"))]
