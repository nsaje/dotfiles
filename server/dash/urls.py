from django.conf.urls import url

from dash import views

urlpatterns = [
    url(r'^login$', 'django.contrib.auth.views.login', {'template_name': 'dash/login.html'})
]
