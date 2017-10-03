from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def index(request):
    return HttpResponse("This is a mock main page for TICA v2 site. Hi.")