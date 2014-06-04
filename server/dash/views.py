from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import redirect

# Create your views here.
def index(request):
	if request.user.is_authenticated():
		return HttpResponse("Hello, world. This is the home of the angular app.")
	else:
		return redirect('/signin')
