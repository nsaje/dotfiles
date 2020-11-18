from django.conf.urls import include
from django.conf.urls import url

import restapi.booksclosed.v1.urls

urlpatterns = [url(r"^v1/booksclosed/", include(restapi.booksclosed.v1.urls, namespace="restapi.booksclosed.v1"))]
