from django.conf.urls import url

import views

urlpatterns = [
    url(
        r'^internal/bluekai/taxonomy/$',
        views.TaxonomyTreeView.as_view(),
        name='internal_bluekai_taxonomy'
    )
]
