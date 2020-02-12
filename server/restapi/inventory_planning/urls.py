from django.conf.urls import include
from django.conf.urls import url

import restapi.inventory_planning.internal.urls

urlpatterns = [
    url(
        r"^internal/inventory-planning/",
        include(restapi.inventory_planning.internal.urls, namespace="restapi.inventory_planning.internal"),
    )
]
