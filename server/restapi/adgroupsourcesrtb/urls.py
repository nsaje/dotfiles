from django.conf.urls import include
from django.conf.urls import url

import restapi.adgroupsourcesrtb.v1.urls

urlpatterns = [
    url(r"^v1/adgroups/", include(restapi.adgroupsourcesrtb.v1.urls, namespace="restapi.adgroupsourcesrtb.v1"))
]
