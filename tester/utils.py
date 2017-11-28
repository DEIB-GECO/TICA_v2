import logging
import os

import numpy as np
import pandas as pd
from django.forms.models import model_to_dict

from tester.models import *

logger = logging.getLogger(__name__)

staticCache = dict()

# path to encode preprocessed data
encode_directory = os.path.join(
    os.path.dirname(os.path.abspath(os.path.dirname(__file__))),
    "media/encode")


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
                temp = nullpd[nullpd['max_distance'] == max_distance].drop(['id', 'cell_line', 'tf1', 'tf2', 'max_distance'
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


def check_tf2(cell, tf1_list, tf2_list, maxd, tail_size, min_tss, min_count, p_value, min_num_true_test, test_list, method='encode', session_id=None):
    temp_null = calculate_null(cell)[maxd]
    result = []
    if method == 'encode':
        null_lines = CellLineNull.objects.filter(cell_line=cell)
    else:
        null_lines = AnalysisResults.objects.filter(session_id=session_id)

    null_lines = null_lines.filter(tf1__in=tf1_list).filter(tf2__in=tf2_list).filter(max_distance=maxd).order_by('tf1', 'tf2')

    print(null_lines.query)

    for line_null in null_lines:

        tf1 = line_null.tf1
        tf2 = line_null.tf2

        line_null_dict = model_to_dict(line_null)

        # start stat testing
        passed = []
        scores = {'name_tf1': tf1,
                  'name_tf2': tf2,
                  "couples": line_null.cumulative_count_all,
                  "couples_tss": line_null.cumulative_count_tss / line_null.cumulative_count_all}
        if (line_null.cumulative_count_all >= min_count) and (line_null.cumulative_count_tss / line_null.cumulative_count_all >= min_tss):

            for i in test_list:
                test_name = i + "-" + str(p_value)
                null_value = temp_null[test_name]
                if line_null_dict[i] is not None and line_null_dict[i] <= null_value:
                    passed.append(i)
                    scores[i + "_passed"] = "Passed"
                else:
                    scores[i + "_passed"] = "Failed"
                scores[i] = line_null_dict[i]

        scores['num_passed'] = len(passed)

        result.append(scores)

    return result
