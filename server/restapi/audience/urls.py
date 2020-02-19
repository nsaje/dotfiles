from django.conf.urls import include
from django.conf.urls import url

import restapi.audience.v1.urls

urlpatterns = [url(r"^v1/accounts/", include(restapi.audience.v1.urls, namespace="restapi.audience.v1"))]
