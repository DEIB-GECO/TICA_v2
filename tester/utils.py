import pandas as pd
import numpy as np

import logging


from tester.models import Hepg2, Hepg2Null

logger = logging.getLogger(__name__)


def calculate_null() :
    #TODO make this list reading from database
    include_list = ['ARID3A', 'ATF4', 'BHLHE40', 'BRCA1', 'CEBPB', 'CEBPD', 'CHD2', 'CREM', 'CTCF', 'DNMT3B', 'DROSHA', 'ELF1', 'EP300', 'ETV4', 'EZH2', 'FOSL2', 'FOXA1', 'FOXA2', 'FOXK2', 'GABPA', 'GATA4', 'GTF2F1', 'HCFC1', 'HDAC2', 'HHEX', 'HLF', 'HNF1A', 'HNF4A', 'HNF4G', 'HNRNPLL', 'HSF1', 'IKZF1', 'IRF3', 'JUND', 'JUN', 'KAT2B', 'MAFF', 'MAX', 'MAZ', 'MBD4', 'MNT', 'MXI1', 'MYBL2', 'MYC', 'NFE2L2', 'NFIC', 'NR2C2', 'NR2F6', 'NRF1', 'PLRG1', 'POLR2A', 'POLR2AphosphoS2', 'POLR2AphosphoS5', 'RAD21', 'RAD51', 'RCOR1', 'REST', 'RFX5', 'RNF2', 'RXRA', 'SIN3A', 'SIN3B', 'SMC3', 'SOX13', 'SP1', 'SREBF1', 'SUZ12', 'TAF1', 'TBP', 'TCF7L2', 'TCF7', 'TEAD4', 'TFAP4', 'USF1', 'USF2', 'YBX1', 'YY1', 'ZBTB40', 'ZBTB7A', 'ZHX2', 'ZKSCAN1', 'ZMYM3', 'ZNF143', 'ZNF207', 'ZNF274', 'ZNF384']
    nullpd = pd.DataFrame(list(Hepg2Null.objects.filter(tf1__in=include_list).filter(tf2__in=include_list).exclude(average__isnull=True).values()))

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
    logger.warning('all_tfs is ready')
    #we need to optimize this
    return list(Hepg2.objects.values_list('tf1',flat=True).distinct()) + list(Hepg2.objects.values_list('tf2',flat=True).distinct())

#lazy val
all_tfs = sorted(list(set(get_all_tfs())))



#for now tail size = 1000
#for now p values are 1,5,10,20
#test_list =  ['average', 'mad', 'median', 'tail_1000']
#example usage -> check_tf('ARID3A',2200,'not_used',0,0,1,4,['average', 'mad', 'median', 'tail_1000'])
def check_tf(tf_in, maxd, tail_size, min_tss, min_count, p_value, min_num_true_test, test_list):
    temp_null = calculated_null[maxd]
    result = []
    for tf in all_tfs:
        if(tf == tf_in):
            continue
        tf1 = tf_in
        tf2 = tf
        if(tf1 > tf2) :
            tf1 = tf
            tf2 = tf_in
        # print(tf1)
        # print(tf2)

        # contains the max line less then or equel to maxd
        #TODO we can select all together, this will be faster
        line = Hepg2.objects.filter(tf1=tf1).filter(tf2=tf2).filter(cumulative_count_all__lte = maxd).order_by('-distance').first()
        line_null = Hepg2Null.objects.filter(tf1=tf1).filter(tf2=tf2).filter(max_distance = maxd).values().first()


        if(line is None):
            continue


        if(line.cumulative_count_all < min_count):
            continue
        if (line.cumulative_count_tss/line.cumulative_count_all < min_tss):
            continue


        passed = []
        for i in test_list:
            test_name = i + "-" + str(p_value)
            null_value = temp_null[test_name]
            if(line_null[i] is None):
                continue
            #TODO check correctness
            if(line_null[i] >= null_value ):
                passed.append(i)
        if(min_num_true_test <= len(passed)):
            result.append((tf,passed))


    # result is list of tuples first element is name of tf and second one is passed test
    return result

