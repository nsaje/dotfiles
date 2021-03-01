from django.conf.urls import include
from django.conf.urls import url

import restapi.realtimestats.beta.urls
import restapi.realtimestats.v1.urls

urlpatterns = [url(r"^beta/", include(restapi.realtimestats.beta.urls, namespace="restapi.realtimestats.beta"))]
urlpatterns += [url(r"^v1/", include(restapi.realtimestats.v1.urls, namespace="restapi.realtimestats.v1"))]
