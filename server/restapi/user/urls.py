from django.conf.urls import include
from django.conf.urls import url

import restapi.user.internal.urls

urlpatterns = [url(r"^internal/users/", include(restapi.user.internal.urls, namespace="restapi.user.internal"))]
