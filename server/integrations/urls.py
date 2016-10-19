from django.conf.urls import url

import integrations.bizwire.views
import integrations.bizwire.internal.views


urlpatterns = [
    url(
        r'^businesswire/promotion_export/',
        integrations.bizwire.views.PromotionExport.as_view()
    ),
    url(
        r'^businesswire/internal/articles/',
        integrations.bizwire.internal.views.article_upload,
    )
]
