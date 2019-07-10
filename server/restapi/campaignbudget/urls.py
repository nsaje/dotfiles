from django.conf.urls import include
from django.conf.urls import url

import restapi.campaignbudget.internal.urls
import restapi.campaignbudget.v1.urls

urlpatterns = [
    url(r"^v1/campaigns/", include(restapi.campaignbudget.v1.urls, namespace="restapi.campaignbudget.v1")),
    url(
        r"^internal/campaigns/",
        include(restapi.campaignbudget.internal.urls, namespace="restapi.campaignbudget.internal"),
    ),
]
