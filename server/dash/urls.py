from django.conf.urls import url

from dash import views
from dash.auth.forms import AuthenticationForm

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^signin$',
        'django.contrib.auth.views.login',
        {'authentication_form': AuthenticationForm, 'template_name': 'dash/signin.html'}),
    url(r'^signout$', 'django.contrib.auth.views.logout_then_login')
]
