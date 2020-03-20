from django.conf.urls import include
from django.conf.urls import url

import restapi.creditrefund.internal.urls

urlpatterns = [
    url(r"^internal/", include(restapi.creditrefund.internal.urls, namespace="restapi.creditrefund.internal"))
]
