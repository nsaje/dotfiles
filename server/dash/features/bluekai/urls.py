from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^internal/bluekai/taxonomy/$',
        views.TaxonomyTreeInternalView.as_view(),
        name='internal_bluekai_taxonomy'
    ),
    url(
        r'^v1/bluekai/taxonomy/$',
        views.TaxonomyTreeView.as_view(),
        name='v1_bluekai_taxonomy'
    ),
    url(
        r'^internal/bluekai/reach/$',
        views.SegmentReachView.as_view(),
        name='internal_bluekai_reach'
    )
]
