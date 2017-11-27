import json
import os
import time

import django_tables2 as tables
from django.db import connections
from django.shortcuts import render
from django_tables2 import RequestConfig

import tester.utils as utils
from tester.pipeline_controller import pipeline_controller
from .forms import *


# Create your views here.
def create_session_id(request):
    ip = str(request.META.get('REMOTE_ADDR'))
    ts = str(time.time())

    return (ip + "_" + ts).replace('.', '_')


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
    # To be verified
    if method == 'encode':
        form = EncodeParameterForm(cell, method,
                                   initial={'max_dist': 2200,
                                            'num_min': 1,
                                            'num_min_w_tsses': 0.01,
                                            'min_test_num': 3,
                                            'which_tests': ['average', 'mad', 'median', 'tail_1000'],
                                            })
    elif method == 'mydata_encode' or method == 'mydata_mydata':
        form = MyDataEncodeParameterForm()
        form.set_initial_values(cell, method, create_session_id(request))


    context = {
        'form': form,
        'http_method': 'get' if method == 'encode' else 'post'
    }
    return render(request, "tester/param_input.html", context=context)


def child(session_id, method, cell):
    pipeline_controller(session_id, method, cell)


def test_results(request):
    method = request.GET['method'] if request.method == 'GET' else request.POST['method']
    if method == 'encode':
        return test_results_encode(request)
    elif method == 'mydata_encode' or method == 'mydata_mydata':
        return test_results_mydata_encode(request)


def test_results_mydata_encode(request):
    if request.method == 'POST':
        cell = request.POST['cell']
        method = request.POST['method']
        session_id = create_session_id(request)

        form = MyDataEncodeParameterForm(request.POST, request.FILES)
        form.set_initial_values(cell,
                                method,
                                session_id)
        if form.is_valid():
            newdoc = MyDataEncodeFormModel(cell=cell,
                                           method=method,
                                           session_id=session_id,
                                           mydata=request.FILES['mydata'])
            newdoc.save()

            connections.close_all()

            pid = os.fork()
            if pid == 0:
                child(session_id, method, cell)
                return

        else:
            print("\n\n\n\n NOT VALID:", form.errors, "\n\n\n\n")

    context = {
        'my_path' : request.get_host() + "/tester/back_to_session/",
        'session_id' : session_id
    }
    return render(request, 'tester/upload_response.html', context=context)


def test_results_encode(request):
    method = request.GET['method']
    session_id = request.GET.get('session_id')
    print(method)
    print(session_id)

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
    all_fields = set(all_tests).union([x + "_passed" for x in all_tests])
    wanted_tests = list(map(lambda s: s.replace('wants_', ''), which_tests))
    not_shown = list(all_fields.difference(set(wanted_tests))
                     .difference(set([x + "_passed" for x in wanted_tests])))

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
                                       wanted_tests,method,session_id)



    table = NameTable(analysis_results)

    heatmap_pairs = {}
    for r in analysis_results:
        heatmap_pairs[(r['name_tf1'], r['name_tf2'])] = r['num_passed']

    list_tf1_r = list(sorted(list(set([x[0] for x in heatmap_pairs.keys()]))))
    list_tf2_r = list(sorted(list(set([x[1] for x in heatmap_pairs.keys()]))))

    json_datasets = []
    for t1 in list_tf1_r:
        values = [heatmap_pairs.get((t1, t2), -1) for t2 in list_tf2_r]
        dataset = {'label': t1, 'data': values}
        json_datasets.append(dataset)

    data_json = str(json.dumps({'labels': list_tf2_r, 'datasets': json_datasets}))

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
        'heatmap': data_json,
    }

    return render(request, 'tester/test_results.html', context)


def back_to_session(request):
    session_id = request.GET['session_id']

    session = MyDataEncodeFormModel.objects.filter(session_id=session_id)

    context = {'session_id' : session_id}

    if not session:
        context['message'] = "Your session was not found :-("
    elif session.count() > 1:
        context['message'] = "Something went wrong, sorry :-( "
    elif session.first().upload_status == 'PENDING':
        context['message'] = "Still processing your file. "  + \
                  "Please come back in a few minutes."
    elif session.first().upload_status == 'FAIL':
        context['message'] = "Something went wrong while processing you file :-("
    else:
        session = session.first()
        cell  = session.cell
        method  = session.method
        form = EncodeParameterForm(cell, method,
                                   initial={'max_dist': 2200,
                                            'num_min': 1,
                                            'num_min_w_tsses': 0.01,
                                            'min_test_num': 3,
                                            'which_tests': ['average', 'mad', 'median', 'tail_1000'],
                                            })
        list_tf1 = sorted(list(AnalysisResults.objects.filter(
            session_id=session_id).values_list('tf1', flat=True).distinct()))
        list_tf2 = sorted(list(AnalysisResults.objects.filter(
            session_id=session_id).values_list('tf2', flat=True).distinct()))
        form.__set_tf1__(list_tf1)
        form.__set_tf2__(list_tf2)
        form.__set_session_id__(session_id)
        context['form'] = form
        context['http_method'] = 'get'

    return render(request, 'tester/user_session.html', context)


