from django.conf.urls import url

import integrations.bizwire.views
import integrations.bizwire.internal.views


urlpatterns = [
    url(
        r'^businesswire/promotion_export/',
        integrations.bizwire.views.PromotionExport.as_view(),
        name='businesswire_promotion_export',
    ),
    url(
        r'^businesswire/internal/articles/',
        integrations.bizwire.internal.views.article_upload,
        name='businesswire_article_upload',
    ),
    url(
        r'^businesswire/internal/click_capping/',
        integrations.bizwire.internal.views.click_capping,
        name='businesswire_click_capping',
    )
]
