from django.conf.urls import url

import views


urlpatterns = [
    url(
        r'internal/inventory-planning/(?P<breakdown>({0}))/?$'.format('|'.join(views.VALID_BREAKDOWNS)),
        views.InventoryPlanningView.as_view(),
        name='inventory_planning'
    ),
]
