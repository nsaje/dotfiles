from django.conf.urls import url

from . import views
from .internal import views as internal_views


urlpatterns = [
    url(
        r'^promotion_export/$',
        views.PromotionExport.as_view(),
        name='businesswire_promotion_export',
    ),
    url(
        r'^internal/articles/$',
        internal_views.article_upload,
        name='businesswire_article_upload',
    ),
    url(
        r'^internal/click_capping/$',
        internal_views.click_capping,
        name='businesswire_click_capping',
    )
]
