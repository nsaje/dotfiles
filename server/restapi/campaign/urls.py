from django.conf.urls import include
from django.conf.urls import url

import restapi.campaign.internal.urls
import restapi.campaign.v1.urls

urlpatterns = [
    url(r"^v1/campaigns/", include(restapi.campaign.v1.urls, namespace="restapi.campaign.v1")),
    url(r"^internal/campaigns/", include(restapi.campaign.internal.urls, namespace="restapi.campaign.internal")),
]
