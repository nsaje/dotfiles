from django.conf.urls import include
from django.conf.urls import url

import restapi.report.v1.urls

urlpatterns = [url(r"^v1/reports/", include(restapi.report.v1.urls, namespace="restapi.report.v1"))]
