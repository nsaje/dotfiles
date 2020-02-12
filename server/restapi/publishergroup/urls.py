from django.conf.urls import include
from django.conf.urls import url

import restapi.publishergroup.v1.urls

urlpatterns = [url(r"^v1/accounts/", include(restapi.publishergroup.v1.urls, namespace="restapi.publishergroup.v1"))]
