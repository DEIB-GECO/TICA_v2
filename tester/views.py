from django.shortcuts import render
from .models import Hepg2

# Create your views here.



def param_input(request):
    return render(request, "tester/param_input.html")


def test_results(request):
    # I need four boolean values
    # if type(request.GET['which_tests']) is not list and 1 <= len(request.GET['which_tests'],) <= 4 \
    #         and any([type(item) is not bool for item in request.GET['which_tests']]):
    #     raise Http404('Test list is not of the correct type')
    test_results = Hepg2.objects.all() # Must be updated with actual query
    context = {
        'tf1': request.GET['tf1'],
        'tf2': request.GET['tf2'],
        'cell': request.GET['cell'],
        'maxdist': request.GET['maxdist'],
        'num_min': request.GET['num_min'],
        'num_min_w_tsses': float(request.GET['num_min_w_tsses']),
        'which_tests': list(map(lambda s: s.replace('wants_', ''), request.GET.getlist('which_tests'))),
        'min_test_num': request.GET['min_test_num'],
        'pvalue': request.GET['pvalue'],
    }
    return render(request, 'tester/test_results.html', context)