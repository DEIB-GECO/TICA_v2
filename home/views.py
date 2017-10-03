from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

test_correspondence = {0:'average',
                       1:'median',
                       2:'mad',
                       3:'tail_size'}


def index(request):
    return HttpResponse("This is a mock main page for TICA v2 site. Hi.")