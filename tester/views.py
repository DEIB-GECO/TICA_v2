from django.shortcuts import render
from .utils import check_tf
from .forms import *
import django_tables2 as tables
from django_tables2 import RequestConfig
import os
import time

# Create your views here.
def create_session_id(request):
    ip = str(request.META.get('REMOTE_ADDR'))
    ts = str(time.time())

    return (ip + "_" + ts).replace('.','_')


def index(request):
    greeting_message = "This is a mock main page for TICA v2 site. " \
              "Hello Arif, I changed the code! =)"

    form = CellMethodForm()
    context = {
        'message': greeting_message,
        'form': form,
    }
    return render(request, 'tester/index.html', context)


def param_input(request):
    method = request.POST['method']
    cell = request.POST['cell']
    initials = {'cell': cell, 'method': method}

    form = None
    if method == 'encode':
        form = EncodeParameterForm(cell,method)
    elif method == 'mydata_encode':
        form = MyDataEncodeParameterForm()
        form.set_initial_values(cell,method,create_session_id(request))
    elif method == 'mydata_mydata':
        pass

    return render(request, "tester/param_input.html", {'form': form})


def child(session_id):

    aaa = Hepg2.objects.first()
    print("\n\n\n\n\n\nchild\n\n\n\n\n", aaa, type(aaa), session_id)
    os._exit(0)


def test_results(request):
    method = request.POST['method']
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
            newdoc.save()
        else:
            print("\n\n\n\n NOT VALID:",form.errors, "\n\n\n\n")

    return render(request, 'tester/job_status.html')


def test_results_encode(request):
    tf1 = request.POST.getlist('tf1')
    tf2 = request.POST.getlist('tf2')
    max_dist = int(request.POST['max_dist'])
    min_test_num = int(request.POST['min_test_num'])
    pvalue = int(request.POST['pvalue'])
    num_min = int(request.POST['num_min'])
    num_min_w_tsses = float(request.POST['num_min_w_tsses'])

    all_fields = set(['average', 'median', 'mad', 'tail_1000'])
    wanted_tests = list(map(lambda s: s.replace('wants_', ''), request.POST.getlist('which_tests')))
    not_shown = list(all_fields.difference(set(wanted_tests)))

    class NameTable(tables.Table):
        name_tf1 = tables.Column()
        name_tf2 = tables.Column()
        average = tables.Column()
        median = tables.Column()
        mad = tables.Column()
        tail_1000 = tables.Column()

        class Meta():
            exclude = not_shown
            attrs = {'class': 'paleblue'}

    context = {
        'tf1': tf1,
        'tf2': tf2,
        'cell': request.POST['cell'],
        'maxdist': max_dist,
        'num_min': num_min,
        'num_min_w_tsses': num_min_w_tsses,
        'which_tests': wanted_tests,
        'min_test_num': min_test_num,
        'pvalue': pvalue,
        'table': None,
    }

    #{% render_table table %}
    return render(request, 'tester/test_results.html', context)

def test_results_2(request):

    print()
    ip = str(request.META.get('REMOTE_ADDR'))
    ts = str(time.time())

    session_id = (ip + "_" + ts).replace('.','_')

    newpid = os.fork()
    if newpid == 0:
        child(session_id=session_id)

    else:
        all_fields = set(['average','median', 'mad', 'tail_1000'])
        wanted_tests = list(map(lambda s: s.replace('wants_', ''), request.POST.getlist('which_tests')))
        not_shown = list(all_fields.difference(set(wanted_tests)))

        class NameTable(tables.Table):
            name_tf1 = tables.Column()
            name_tf2 = tables.Column()
            average = tables.Column()
            median = tables.Column()
            mad = tables.Column()
            tail_1000 = tables.Column()

            class Meta():
                exclude = not_shown
                attrs = {'class': 'paleblue'}


        print("\n\n\n",request.POST['docfile'],"\n\n\n\n")

        # I need four boolean values
        # if type(request.GET['which_tests']) is not list and 1 <= len(request.GET['which_tests'],) <= 4 \
        #         and any([type(item) is not bool for item in request.GET['which_tests']]):
        #     raise Http404('Test list is not of the correct type')
        test_results = Hepg2.objects.all() # Must be updated with actual query

        tf1 = request.POST['tf1']
        max_dist = int(request.POST['max_dist'])
        min_test_num = int(request.POST['min_test_num'])
        pvalue = int(request.POST['pvalue'])
        num_min = int(request.POST['num_min'])
        num_min_w_tsses = float(request.POST['num_min_w_tsses'])
        table = NameTable(
            check_tf(tf1,
                     max_dist,
                     'not_used',
                     num_min_w_tsses,
                     num_min,
                     pvalue,
                     min_test_num,
                     wanted_tests)
        )
        RequestConfig(request).configure(table)
        context = {
            'tf1': tf1,
            'cell': request.POST['cell'],
            'maxdist': max_dist,
            'num_min': num_min,
            'num_min_w_tsses': num_min_w_tsses,
            'which_tests': wanted_tests,
            'min_test_num': min_test_num,
            'pvalue': pvalue,
            'table' : table,
        }
        return render(request, 'tester/test_results.html', context)