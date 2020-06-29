from django.conf.urls import include
from django.conf.urls import url

import restapi.videoassets.v1.urls

urlpatterns = [url(r"^v1/accounts/", include(restapi.videoassets.v1.urls, namespace="restapi.videoassets.v1"))]
