from django.conf.urls import url

from dash import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^signin$', 'django.contrib.auth.views.login', {'template_name': 'dash/signin.html'}),
    url(r'^signout$', 'django.contrib.auth.views.logout_then_login')
]
