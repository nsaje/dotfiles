from django.conf.urls import include
from django.conf.urls import url

import restapi.adgroupstats.v1.urls

urlpatterns = [url(r"^v1/adgroupstats/", include(restapi.adgroupstats.v1.urls, namespace="restapi.adgroupstats.v1"))]
