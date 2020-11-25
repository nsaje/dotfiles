from django.conf.urls import include
from django.conf.urls import url

import restapi.bulkupload.beta.urls

urlpatterns = [
    url(r"^beta/bulkupload/", include(restapi.bulkupload.beta.urls, namespace="restapi.bulkupload.beta.adgroups"))
]
