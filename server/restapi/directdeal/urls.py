from django.conf.urls import include
from django.conf.urls import url

import restapi.directdeal.internal.urls

urlpatterns = [
    url(
        r"^internal/agencies/(?P<agency_id>\d+)/deals/",
        include(restapi.directdeal.internal.urls, namespace="restapi.directdeal.internal"),
    )
]