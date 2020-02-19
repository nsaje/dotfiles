from django.conf.urls import url

from restapi.inventory_planning.internal import views

app_name = "restapi.inventory-planning"
urlpatterns = [
    url(
        r"^(?P<breakdown>({0}))/?$".format("|".join(views.VALID_BREAKDOWNS)),
        views.InventoryPlanningView.as_view({"get": "get", "post": "post"}),
        name="inventory_planning",
    ),
    url(r"^export/?$", views.InventoryPlanningView.as_view({"post": "export"}), name="inventory_planning_export"),
]
