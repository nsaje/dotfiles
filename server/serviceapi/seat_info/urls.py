from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^seatinfo/accounts/(?P<seat_id>\d+)$", views.SeatInfoView.as_view(), name="service.seatinfo.seats")
]
