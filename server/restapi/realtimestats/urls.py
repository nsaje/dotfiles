from django.conf.urls import include
from django.conf.urls import url

import restapi.realtimestats.beta.urls

urlpatterns = [url(r"^beta/", include(restapi.realtimestats.beta.urls, namespace="restapi.realtimestats.beta"))]
