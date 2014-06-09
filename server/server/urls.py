from django.conf.urls import patterns, include, url
from django.contrib import admin

from dash import views as dash_views
from zemauth.forms import AuthenticationForm

urlpatterns = patterns(
    '',
    url(r'^$', dash_views.index, name='index'),
    url(r'^signin$',
        'django.contrib.auth.views.login',
        {'authentication_form': AuthenticationForm, 'template_name': 'zemauth/signin.html'}),
    url(r'^signout$', 'django.contrib.auth.views.logout_then_login'),
    url(r'^admin/', include(admin.site.urls))
)
