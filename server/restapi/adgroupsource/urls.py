from django.conf.urls import include
from django.conf.urls import url

import restapi.adgroupsource.v1.urls

urlpatterns = [url(r"^v1/adgroups/", include(restapi.adgroupsource.v1.urls, namespace="restapi.adgroupsource.v1"))]
