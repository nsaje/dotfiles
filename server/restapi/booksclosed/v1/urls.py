from django.conf.urls import url

from . import views

app_name = "restapi.booksclosed"
urlpatterns = [url(r"^$", views.BooksClosedViewSet.as_view({"get": "get"}), name="booksclosed")]
