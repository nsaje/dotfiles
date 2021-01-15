from django.conf.urls import include
from django.conf.urls import url

import restapi.creative_tags.internal.urls

urlpatterns = [
    url(
        r"^internal/creativetags/",
        include(restapi.creative_tags.internal.urls, namespace="restapi.creative_tags.internal"),
    )
]
