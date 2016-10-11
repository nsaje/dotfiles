from django.conf.urls import url

import integrations.bizwire.views


urlpatterns = [
    url(
        r'^businesswire/promotion_export/',
        integrations.bizwire.views.PromotionExport.as_view()
    ),
]
