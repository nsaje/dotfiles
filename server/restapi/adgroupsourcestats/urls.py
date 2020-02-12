from django.conf.urls import include
from django.conf.urls import url

import restapi.adgroupsourcestats.v1.urls

urlpatterns = [
    url(
        r"^v1/adgroupsourcestats/",
        include(restapi.adgroupsourcestats.v1.urls, namespace="restapi.adgroupsourcestats.v1"),
    )
]
