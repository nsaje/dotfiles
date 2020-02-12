from django.conf.urls import include
from django.conf.urls import url

import restapi.campaignstats.v1.urls

urlpatterns = [url(r"^v1/campaignstats/", include(restapi.campaignstats.v1.urls, namespace="restapi.campaignstats.v1"))]
