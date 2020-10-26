from django.conf.urls import include
from django.conf.urls import url

import restapi.adgroupsourcestats.internal.urls
import restapi.adgroupsourcestats.v1.urls

urlpatterns = [
    url(r"^v1/adgroups/", include(restapi.adgroupsourcestats.v1.urls, namespace="restapi.adgroupsourcestats.v1")),
    url(
        r"^internal/adgroups/",
        include(restapi.adgroupsourcestats.internal.urls, namespace="restapi.adgroupsourcestats.internal"),
    ),
]
