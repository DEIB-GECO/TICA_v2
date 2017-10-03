from django.shortcuts import render
from django.http import HttpResponse, Http404
from .models import Hepg2

# Create your views here.

test_correspondence = {0:'average',
                       1:'median',
                       2:'mad',
                       3:'tail_size'}


def param_input(request):
    return HttpResponse("This is a mock main page for testing using TICA_v2.")


def test_results(request, tf1, tf2, cell, maxdistance, pvalue, tail_size,
         which_tests, min_test_num):
    # I need four boolean values
    if type(which_tests) is not list and 1 <= len(which_tests) <= 4 \
            and any([type(item) is not bool for item in which_tests]):
        raise Http404('Test list is not of the correct type')
    test_results = Hepg2.objects.all() # Must be updated with actual query
    response = 'The test on TFs %s and %s in cell line %s gives\n ' \
               'the following results:\n' \
               'maxdistance: %d\n' \
               'tests used: %s\n' \
               'pvalue: %f\n' \
               'test rejects needed: at least %d\n' \
               'result: TBD'
    return HttpResponse(response % (tf1, tf2, cell, maxdistance,
                     map(lambda t: test_correspondence[t], which_tests),
                     pvalue, min_test_num))