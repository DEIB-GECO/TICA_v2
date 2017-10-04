from django.shortcuts import render
from .models import Hepg2
from .utils import check_tf
import django_tables2 as tables

# Create your views here.



def param_input(request):
    return render(request, "tester/param_input.html")


def test_results(request):

    all_fields = set(['average','median', 'mad', 'tail_1000'])
    wanted_tests = list(map(lambda s: s.replace('wants_', ''), request.GET.getlist('which_tests')))
    not_shown = list(all_fields.difference(set(wanted_tests)))

    class NameTable(tables.Table):
        name = tables.Column()
        average = tables.Column()
        median = tables.Column()
        mad = tables.Column()
        tail_1000 = tables.Column()

        class Meta():
            exclude = not_shown
            attrs = {'class': 'paleblue'}




    # I need four boolean values
    # if type(request.GET['which_tests']) is not list and 1 <= len(request.GET['which_tests'],) <= 4 \
    #         and any([type(item) is not bool for item in request.GET['which_tests']]):
    #     raise Http404('Test list is not of the correct type')
    test_results = Hepg2.objects.all() # Must be updated with actual query

    tf1 = request.GET['tf1']
    maxdist = int(request.GET['maxdist'])
    min_test_num = int(request.GET['min_test_num'])
    pvalue = int(request.GET['pvalue'])
    num_min = int(request.GET['num_min'])
    num_min_w_tsses = float(request.GET['num_min_w_tsses'])
    context = {
        'tf1': tf1,
        'cell': request.GET['cell'],
        'maxdist': maxdist,
        'num_min': num_min,
        'num_min_w_tsses': num_min_w_tsses,
        'which_tests': list(map(lambda s: s.replace('wants_', ''), request.GET.getlist('which_tests'))),
        'min_test_num': min_test_num,
        'pvalue': pvalue,
        'table' : NameTable(
            check_tf(tf1,
                     maxdist,
                     'not_used',
                     num_min_w_tsses,
                     num_min,
                     pvalue,
                     min_test_num,
                     wanted_tests)
        ),
    }
    return render(request, 'tester/test_results.html', context)