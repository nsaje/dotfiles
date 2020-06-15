from django.conf.urls import include
from django.conf.urls import url

import restapi.rules.internal.urls

urlpatterns = [url(r"^internal/rules/", include(restapi.rules.internal.urls, namespace="restapi.rules.internal"))]
