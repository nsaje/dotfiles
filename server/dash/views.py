from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from django.conf import settings


# Create your views here.
@login_required(login_url=settings.LOGIN_URL)
def index(request):
    return render(request, 'index.html', {'staticUrl': settings.CLIENT_STATIC_URL})
