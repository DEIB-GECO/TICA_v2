import pandas as pd
import numpy as np

import logging


from tester.models import Hepg2, Hepg2Null

logger = logging.getLogger(__name__)


def calculate_null() :
    nullpd = pd.DataFrame(list(Hepg2Null.objects.exclude(average__isnull=True).values()))

    max_distances = sorted(nullpd.reset_index()['max_distance'].unique())

    bootsrapt_size = 10000
    nullpds = {}
    percs = [1, 5, 10, 20]
    for max_distance in max_distances:
        temp = nullpd[nullpd['max_distance'] == max_distance].drop(['tf1', 'tf2', 'max_distance'], axis=1)
        temp = temp.sample(bootsrapt_size, replace=True)
        x = []
        names = []
        for col in temp.columns:
            temp1 = (temp[col])
            tempavgs = [np.percentile(temp1, q=perc) for perc in percs]
            x = x + tempavgs

            nms = [col + "-" + str(perc) for perc in percs]
            names = names + nms
        nullpds[max_distance] = x
    logger.warning('calculated_null is ready')

    result = pd.DataFrame(nullpds, index=names)
    # return result # OR POSSIBLY .to_dict #THAT GENERATED TWO LEVEL OF DICTIONARY, MAXD, AND THEN NAME THAT GENERATED BEFORE
    return result.to_dict() #THAT GENERATED TWO LEVEL OF DICTIONARY, MAXD, AND THEN NAME THAT GENERATED BEFORE

#LAZY VAL
calculated_null = calculate_null()
def get_all_tfs() :
    return list(Hepg2.objects.values_list('tf1',flat=True).distinct())

#lazy val
all_tfs = get_all_tfs()



#for now tail size = 1000
#for now p values are 1,5,10,20
def check_tf(tf_in, maxd, tail_size, min_tss, min_count, p_value, min_num_true_test):
    temp_null = calculated_null[maxd]
    result = []
    for tf in all_tfs:
        if(tf == tf_in):
            pass
        tf1 = tf_in
        tf2 = tf
        if(tf1 > tf2) :
            tf1 = tf
            tf2 = tf_in
        # contains the max line less then or equel to maxd
        line = Hepg2.objects.filter(tf1=tf1).filter(tf2=tf2).filter(cumulative_count_all__lte = maxd).order_by('-distance').first()
        line_null = Hepg2Null.objects.filter(tf1=tf1).filter(tf2=tf2).filter(max_distance = maxd).values().first()

        if(line.cumulative_count_all < min_count):
            pass
        if (line.cumulative_count_tss/line.cumulative_count_all < min_tss):
            pass


        passed = []
        for i in ['average', 'mad', 'median', 'tail_1000']:
            test_name = i + "-" + str(p_value)
            null_value = temp_null[test_name]
            if(line_null[i] >= null_value ):
                passed.append(i)
        if(min_num_true_test <= len(passed)):
            result.append((tf,passed))


    # result is list of tuples first element is name of tf and second one is passed test
    return result

