from django.conf.urls import include
from django.conf.urls import url

import restapi.source.internal.urls

urlpatterns = [
    url(
        r"^internal/agencies/(?P<agency_id>\d+)/sources/",
        include(restapi.source.internal.urls, namespace="restapi.source.internal"),
    )
]
