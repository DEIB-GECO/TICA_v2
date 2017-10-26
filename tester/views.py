from django.shortcuts import render
import tester.utils as utils
from .forms import *
import django_tables2 as tables
from django_tables2 import RequestConfig
import os
import time
import json

# Create your views here.
def create_session_id(request):
    ip = str(request.META.get('REMOTE_ADDR'))
    ts = str(time.time())

    return (ip + "_" + ts).replace('.','_')


def index(request):

    form = CellMethodForm()
    context = {
        'form': form,
    }
    return render(request, 'tester/index.html', context)


def param_input(request):
    method = request.GET['method']
    cell = request.GET['cell']

    form = None
    if method == 'encode':
        form = EncodeParameterForm(cell,method)
    elif method == 'mydata_encode':
        form = MyDataEncodeParameterForm()
        form.set_initial_values(cell,method,create_session_id(request))
    elif method == 'mydata_mydata':
        pass

    context = {
        'form' : form,
        'http_method' : 'get' if method == 'encode' else 'post'
    }
    return render(request, "tester/param_input.html", context=context)


def child(session_id):

    aaa = Hepg2.objects.first()
    print("\n\n\n\n\n\nchild\n\n\n\n\n", aaa, type(aaa), session_id)
    os._exit(0)


def test_results(request):
    method = request.GET['method']
    if method == 'encode':
        return test_results_encode(request)
    elif method == 'mydata_encode':
        return test_results_mydata_encode(request)


def test_results_mydata_encode(request):
    if request.method == 'POST':
        form = MyDataEncodeParameterForm(request.POST, request.FILES)
        form.set_initial_values(request.POST['cell'],
                                request.POST['method'],
                                request.POST['session_id'])
        if form.is_valid():
            newdoc = MyDataEncodeFormModel(mydata=request.FILES['mydata'])
            newdoc.mydata.upload_to = "uploaded/session_id/"
            newdoc.save()
        else:
            print("\n\n\n\n NOT VALID:",form.errors, "\n\n\n\n")

    return render(request, 'tester/job_status.html')


def test_results_encode(request):
    cell = request.GET['cell']
    tf1 = request.GET.getlist('tf1')
    tf2 = request.GET.getlist('tf2')
    max_dist = int(request.GET['max_dist'])
    min_test_num = int(request.GET['min_test_num'])
    pvalue = int(request.GET['pvalue'])
    which_tests = request.GET.getlist('which_tests')
    num_min = int(request.GET['num_min'])
    num_min_w_tsses = float(request.GET['num_min_w_tsses'])

    all_tests = ['average', 'median', 'mad', 'tail_1000']
    all_fields = set(all_tests).union([x+"_passed" for x in all_tests])
    wanted_tests = list(map(lambda s: s.replace('wants_', ''), which_tests))
    not_shown = list(all_fields.difference(set(wanted_tests))
                     .difference(set([x+"_passed" for x in wanted_tests])))

    class NameTable(tables.Table):
        name_tf1 = tables.Column()
        name_tf2 = tables.Column()
        average = tables.Column()
        average_passed = tables.Column()
        median = tables.Column()
        median_passed = tables.Column()
        mad = tables.Column()
        mad_passed = tables.Column()
        tail_1000 = tables.Column()
        tail_1000_passed = tables.Column()

        class Meta():
            exclude = not_shown
            attrs = {'class': 'paleblue'}

    analysis_results = utils.check_tf2(cell,
                        tf1,
                        tf2,
                        max_dist,
                        'not_used',
                        num_min_w_tsses,
                        num_min,
                        pvalue,
                        min_test_num,
                        wanted_tests)

    table = NameTable(analysis_results)

    heatmap_pairs = {}
    for r in analysis_results:
        heatmap_pairs[(r['name_tf1'], r['name_tf2'])]  = r['num_passed']

    list_tf1_r = list(sorted(list(set([x[0] for x in heatmap_pairs.keys()]))))
    list_tf2_r = list(sorted(list(set([x[1] for x in heatmap_pairs.keys()]))))

    json_datasets = []
    for t1 in list_tf1_r:
        values = [heatmap_pairs.get((t1,t2), -1) for t2 in list_tf2_r]
        dataset = {'label': t1, 'data' : values}
        json_datasets.append(dataset)

    data_json = str(json.dumps({'labels': list_tf2_r, 'datasets' : json_datasets}))

    RequestConfig(request).configure(table)
    context = {
        'tf1': tf1,
        'tf2': tf2,
        'cell': cell,
        'maxdist': max_dist,
        'num_min': num_min,
        'num_min_w_tsses': num_min_w_tsses,
        'which_tests': wanted_tests,
        'min_test_num': min_test_num,
        'pvalue': pvalue,
        'table': table,
        'heatmap' : data_json,
    }

    return render(request, 'tester/test_results.html', context)

