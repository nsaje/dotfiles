from django.conf.urls import url

import views


urlpatterns = [
    url(
        r'^businesswire_promotion_export/',
        views.PromotionExport.as_view()
    ),
]
