import pandas as pd
import numpy as np

import logging
from django.forms.models import model_to_dict
from django.db.models import Q

from tester.models import *

logger = logging.getLogger(__name__)

staticCache = dict()


def get_cell_lines():
    if not 'get_cell_lines' in staticCache:
        staticCache['get_cell_lines'] = list(CellLineTfs.objects.values_list('cell_line', flat=True)
                                             .distinct().order_by('cell_line'))
    return staticCache['get_cell_lines']


def calculate_null(cell='hepg2'):
    if not 'calculate_null-' + cell in staticCache:
        def calc():
            # TODO make this list reading from database
            include_list = list(
                CellLineTfs.objects.filter(cell_line=cell).filter(use_in_null=True).values_list('tf', flat=True))

            nullpd = pd.DataFrame(list(CellLineNull.objects.filter(cell_line=cell).filter(tf1__in=include_list)
                                       .filter(tf2__in=include_list).exclude(average__isnull=True).values()))

            max_distances = sorted(nullpd.reset_index()['max_distance'].unique())

            bootsrapt_size = 10000
            nullpds = {}
            percs = [1, 5, 10, 20]
            for max_distance in max_distances:
                temp = nullpd[nullpd['max_distance'] == max_distance].drop(['cell_line_id', 'tf1', 'tf2', 'max_distance'
                                                                            # ,'cumulative_count_all','cumulative_count_tss'
                                                                            ], axis=1)
                # temp = temp.sample(bootsrapt_size, replace=True)
                x = []
                names = []
                for col in temp.columns:
                    # print(col)
                    temp1 = (temp[col])
                    tempavgs = [np.percentile(temp1, q=perc) for perc in percs]
                    x = x + tempavgs

                    nms = [col + "-" + str(perc) for perc in percs]
                    names = names + nms
                nullpds[max_distance] = x
            # logger.warning('calculated_null is ready')

            result = pd.DataFrame(nullpds, index=names)
            return result.to_dict()

        staticCache['calculate_null-' + cell] = calc()
    return staticCache['calculate_null-' + cell]


def get_tf_list(cell='hepg2'):
    if not 'get_tf_list-' + cell in staticCache:
        staticCache['get_tf_list-' + cell] = list(CellLineTfs.objects.filter(cell_line=cell)
                                                  .values_list('tf', flat=True).order_by('tf'))
    return staticCache['get_tf_list-' + cell]


# for now tail size = 1000
# for now p values are 1,5,10,20
# test_list =  ['average', 'mad', 'median', 'tail_1000']
# example usage -> check_tf('hepg2', 'ARID3A',2200,'not_used',0,0,1,4,['average', 'mad', 'median', 'tail_1000'])
def check_tf(cell, tf_in, maxd, tail_size, min_tss, min_count, p_value, min_num_true_test, test_list):
    temp_null = calculate_null(cell)[maxd]
    result = []
    null_lines = CellLineNull.objects.filter(cell_line=cell).filter(Q(tf1=tf_in) | Q(tf2=tf_in)).filter(
        max_distance=maxd)

    for line_null in null_lines:

        # tf1 = line_null.tf1
        # tf2 = line_null.tf2

        tf = line_null.tf1 if tf_in is not line_null.tf1 else line_null.tf2

        # print(tf1)
        # print(tf2)

        # contains the max line less then or equal to maxd
        # TODO we can select all together, this will be faster
        # line = CellLineCouple.objects.filter(cell_line=cell).filter(tf1=tf1).filter(tf2=tf2).filter(distance__lte=maxd).order_by('-distance').first()
        line_null_dict = model_to_dict(line_null)

        # print(line_null.cumulative_count_all)

        if line_null.cumulative_count_all <= min_count:
            continue
        if line_null.cumulative_count_tss / line_null.cumulative_count_all < min_tss:
            continue

        # start stat testing
        passed = []
        scores = {}
        for i in test_list:
            test_name = i + "-" + str(p_value)
            null_value = temp_null[test_name]
            if line_null_dict[i] is not None and line_null_dict[i] <= null_value:
                passed.append(i)
            scores[i] = line_null_dict[i]
        if min_num_true_test <= len(passed):
            scores['name'] = tf
            result.append(scores)

    # result is list of tuples first element is name of tf and second one is passed test
    return result


def check_tf2(cell, tf1_list, tf2_list, maxd, tail_size, min_tss, min_count, p_value, min_num_true_test, test_list):
    temp_null = calculate_null(cell)[maxd]
    result = []
    null_lines = CellLineNull.objects.filter(cell_line=cell).filter(
        (Q(tf1__in=tf1_list) & Q(tf2__in=tf2_list)) | (Q(tf1__in=tf2_list) & Q(tf2__in=tf1_list))).filter(
        max_distance=maxd)

    for line_null in null_lines:

        # tf1 = line_null.tf1
        # tf2 = line_null.tf2

        tf1 = line_null.tf1
        tf2 = line_null.tf2

        # print(tf1)
        # print(tf2)

        # contains the max line less then or equal to maxd
        # TODO we can select all together, this will be faster
        # line = CellLineCouple.objects.filter(cell_line=cell).filter(tf1=tf1).filter(tf2=tf2).filter(distance__lte=maxd).order_by('-distance').first()
        line_null_dict = model_to_dict(line_null)

        # print(line_null.cumulative_count_all)

        if (line_null.cumulative_count_all <= min_count):
            continue
        if (line_null.cumulative_count_tss / line_null.cumulative_count_all < min_tss):
            continue

        # start stat testing
        passed = []
        scores = {}
        for i in test_list:
            test_name = i + "-" + str(p_value)
            null_value = temp_null[test_name]
            if line_null_dict[i] is not None and line_null_dict[i] <= null_value:
                passed.append(i)
            scores[i] = line_null_dict[i]
        if (min_num_true_test <= len(passed)):
            scores['name'] = tf1 + " - " + tf2
            result.append(scores)

    # result is list of tuples first element is name of tf and second one is passed test
    return result
