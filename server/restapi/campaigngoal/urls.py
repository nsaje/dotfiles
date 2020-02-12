from django.conf.urls import include
from django.conf.urls import url

import restapi.campaigngoal.v1.urls

urlpatterns = [url(r"^v1/campaigns/", include(restapi.campaigngoal.v1.urls, namespace="restapi.campaigngoal.v1"))]
