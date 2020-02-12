from django.conf.urls import include
from django.conf.urls import url

import restapi.publishergroupentry.v1.urls

urlpatterns = [
    url(
        r"^v1/publishergroups/",
        include(restapi.publishergroupentry.v1.urls, namespace="restapi.publishergroupentry.v1"),
    )
]
