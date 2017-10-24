"""Contains the pipeline chuncks which are used by the controller to
 manage the TICA workflow. Please refer to each function for a
 description.
 
NOTE: this script require the existance of one metadata attribute
'TF_name' in all input datasets, which contains the gene symbol of the
TF which they contain.

Author: Stefano Perna (stefano.perna@polimi.it)
Date: 18 October 2017
Version: 0.1"""
#from models import *
from django.forms.models import model_to_dict
from django.db.models import Q
#from tester.models import *

import sys
import gmql as pygmql
import copy
import numpy as np
import pandas as pd
import intervaltree as it
import os
import shutil
import zipfile

# Chromosome names
CHRS = list(map(lambda x: "chr" + str(x), range(1, 23))) + ["chrX", "chrY"]
STATIC_CACHE = dict()

# Common functions
# def __format_checker__(file):
#     """Ancillary function of data_uploader. Returns a string
#     based on the format inspected in the file:
#     - 'narrowPeak': the file suits the ENCODE narrowPeak
#      specifications
#      - 'BED2': the file contains chromosome and start information
#      only,
#      - 'BED3': the file contains chromosome, start and stop
#      information,
#      - 'BED4': the file contains chromosome, start, stop and strand
#      information
#      - 'unknown_format': anything else.
#     """
#     with open(file, 'r') as infile:
#         raw_data = list(infile.readlines)
#     # default separator is assumed to be \t
#     separator = '\t'
#     # comment is #
#     comment_search = [item[0] == '#' for item in raw_data]
#     if all(comment_search):
#         return 'unknown_format'
#     else:
#         true_indexes = [comment_search[i] == False
#                         for i in range(len(comment_search))]
#         if ';' in comment_search[true_indexes[0]] and \
#                         separator not in comment_search[true_indexes[0]]:
#             separator=';'
#         elif ',' in comment_search[true_indexes[0]] \
#                 and separator not in comment_search[true_indexes[0]]:
#             sep=','
#         all_data = pd.read_csv(file,sep=separator, comment='#')
#         if True:
#             return 'narrowPeak'
#             #list of narrowpeak specifications
#         elif all([item in CHRS for item in all_data[0]]) \
#                 and type(all_data[1]) == int \
#                 and type(all_data[2]) == int \
#                 and type(all_data[3]) == str:
#             return 'BED4'
#         elif all([item in CHRS for item in all_data[0]]) \
#                 and type(all_data[1]) == int \
#                 and type(all_data[2]) == int:
#             return 'BED3'
#         elif all([item in CHRS for item in all_data[0]]) \
#                 and type(all_data[1]) == int:
#             return 'BED2'
#         else:
#             return 'unknown_format'
    
    
def data_uploader(input_zip, target_folder='path/to/default'):
    """Loads datasets from the disk and returns formatted GMQLDatasets.
    Keyword arguments:
        -- input_zip: path to zip file containing files, to be
        accessed on disk (default: None)
    """
    
    # TMP
    TMP_FILE_PATH = 'tmp/'
    if not os.path.exists(TMP_FILE_PATH):
        os.makedirs(TMP_FILE_PATH)
        
    assert input_zip, "ERROR: no input file. Aborting."
    
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
        
    with zipfile.ZipFile(input_zip,'r') as zip_ref:
        zip_ref.extractall(TMP_FILE_PATH)
    
    # Assume the zip folder contains one folder for each TF - no enclosing
    # folder.
    tf_folder = list(os.walk(TMP_FILE_PATH))
    
    #childs = [item for item in tf_folder[0][1] if not item.startswith('__')]
    
    #if not list(os.walk('%s/%s/' % (TMP_FILE_PATH, childs[0])))[0][2]:
    #    tf_folder=list(os.walk('%s/%s' % (TMP_FILE_PATH,
    #                                      tf_folder[0][1][-1])))
    #print(tf_folder)
    
    tf_list = list(filter(lambda s: not s.startswith('__'), tf_folder[0][1]))
    
    for tf in tf_list:     # They are also folder names
        for (dir, _, files) in os.walk('%s%s' % (TMP_FILE_PATH, tf)):
            for index, file in enumerate(
                    [item for item in files if not item.startswith('.')]
            ):
                shutil.copy('%s/%s' % (dir, file), '%s/%s_%d.bed' % (
                    target_folder, tf, index)
                            )
                with open('%s/%s_%d.bed.meta' % (
                    target_folder, tf, index),'w') as metafile:
                    metafile.write('experiment_target\t%s\n' % tf)
    shutil.rmtree(TMP_FILE_PATH)
    #os.remove(input_zip)
    return tf_list


def tfbs_filter(datasets, tf_list, window_size=1000, min_acc_value=3):
    """Filters binding sites according to accumulation values in the
    moving window.
    Keyword arguments:
        -- datasets: GMQLDatasets containing TFBSes
        -- window_size: width of the moving window used to filter TFBS
        (default: 1000 [from TICAv1])
        -- min_acc_value: minimum number of TFBSes from the same TFs
        to be found in the moving window (default: 3)
    """
    # Assume tf_list is sorted
    # Assume that input is loaded
    
    # ds_list = []
    #
    # for index in range(len(tf_list)):
    #     ds_list.append(datasets[index].to_GMQLDataset())
    
    # First process the simple ones in batch
    tfbs_data = datasets[0]
    for df in datasets[1:]:
        tfbs_data = tfbs_data.union(df)

    npeaks = tfbs_data.reg_project(
        new_field_dict={
            'start': tfbs_data.start + tfbs_data.peak,
            'stop': tfbs_data.start
                    + tfbs_data.peak + 1}
    )

    # NOTE: groupBy must be given in list format
    covered = npeaks.cover(1, 'ANY', groupBy=['experiment_target'])

    signals = covered
    # Enlarge by moving window
    windows = covered.reg_project(new_field_dict={'start': covered.start
                                                           - window_size,
                                                  'stop': covered.stop
                                                          + window_size})
    m_windows = windows.map(signals, joinBy=['experiment_target'],
                            refName='windows', expName='signals')
    m_windows_filtered = m_windows.reg_select(
        m_windows.count_windows_signals >= min_acc_value
    )
    filtered_signals = m_windows_filtered.reg_project(new_field_dict={
        'start': covered.start + window_size,
        'stop': covered.stop - window_size}
    )

    # For testing purposes
    # filtered_signals.materialize(output_path='simple_tfs/')
    
    return filtered_signals


def tfbs2tss_mapper(tfbs_file_list, target_list,
                    tss_file_path, target_folder='path/to/default'):
    """Maps TFBSes to promoters of TSSes using IDs. Stores maps as
    comma-separated-values on disk and returns them as dicts (?).
    Keyword arguments:
        -- datasets: GMQLDatasets containing TFBSes
        -- tss_dataset: GMQLDataset containing TSSes
        -- target_folder: folder where TFBS_to_TSS maps will be stored
        (default: 'path/to/default')
    """
    # Assume that input is loaded
    # Assume that tfbs file list is sorted according to target_list
    # Parse and load configuration variables

    # Load TSS information from file
    tsses_raw = pd.read_csv(tss_file_path, sep='\t', header=None).values
    tsses = dict(
        [
            (c, [item for item in tsses_raw if item[1] == c])
            for c in CHRS
        ]
    )
    
    to_execute = zip(target_list, tfbs_file_list)
    
    for item in to_execute:
        tfbses_raw_0 = pd.read_csv(item[1],
                                 sep='\t', header=None)
        tfbses_raw_v = [item.tolist() for item in tfbses_raw_0.values]
        tfbses_raw_in = tfbses_raw_0.index
        
        tfbses_raw = list(zip(tfbses_raw_in, tfbses_raw_v))
        tfbses = dict(
            [
                (c, [item for item in tfbses_raw if item[1][0] == c])
                for c in CHRS
            ]
        )
        associated_tss = []
        for c in CHRS:
            f_tfbses = tfbses[c]
            f_tss = it.IntervalTree.from_tuples(
                [(item[2] - 2000, item[3] + 201, item[0])
                 if item[6] == '+'
                 else (item[2] - 200, item[3] + 2001, item[0])
                 for item in tsses[c]]
            )
            c_map_ = [(tfbs[1][0], tfbs[1][1], f_tss[tfbs[1][1]])
                      for tfbs in f_tfbses]
            associated_tss += c_map_
        print(associated_tss)
        with open('%s/%s_TFBS_w_MAPS.tsv' %
                          (target_folder, item[0]), 'w') \
                as associated_outfile:
            
            associated_outfile.writelines(
                ['%s\t%d\t%s\n' %
                 (item[0], item[1], ','.join([str(tss_id)
                                     for tss_id in sorted(
                         [data[2] for data in list(item[2])])])
                 if list(item[2]) else '')
                 for item in associated_tss])
        print('Map complete.')
    return True



# Algorithmic workflow-only
def tss_filter(tss_file_path, cell_name, list_of_targets,
               exon_length=200,
               promoter_length=2000, enhancer_length=1000000,
               min_tfbs_count=50):
    """Filters transcription start sites according to the presence of
    histone marks and the count of TFBS from the same cell line found
    in the promoter of each TSS.
    Keyword arguments:
        -- tss_file_path: path to tss file for loading
        -- cell_name: biosample term name of the context cell line
        -- list_of_target: list of TFs used for filtering non
        actively transcribed promoters
        -- exon_length: standardized downstream extension of each
        exon (default: 200)
        -- promoter_length: standardized upstream extension of each
        promoter (default: 2000)
        -- enhancer_length: standardized upstream extension of each
        enhancer (default: 100000)
        -- min_tfbs_count: minimum number of TFBSes from the same cell
        to be found in the promoter of a valid TSS (default: 50)
    """
    
    # paths to ENCODE datasets
    BROAD_PATH = '/Volumes/PERNA/ENC_broad_Aug_2017/'
    NARROW_PATH = '/Volumes/PERNA/ENC_narrow_Aug_2017/'


    # for testing purposes
    OUTFILE_PATH = 'test_2/'


    # Data loading
    enc_broad_full = pygmql.load_from_path(
        local_path=BROAD_PATH,
        parser=pygmql.parsers.BedParser(chrPos=0,
                                        startPos=1,
                                        stopPos=2)
    )
    enc_narrow_full = pygmql.load_from_path(
        local_path=NARROW_PATH,
        parser=pygmql.parsers.NarrowPeakParser()
    )

    tss_full = pygmql.load_from_path(
        local_path=tss_file_path,
        parser=pygmql.parsers.BedParser(chrPos=0,
                                        startPos=1,
                                        stopPos=2,
                                        strandPos=5)
    )

    # Found on actively transcribed genes
    hm_4_exons = enc_broad_full[
        (enc_broad_full['assay'] == 'ChIP-seq')
        & (enc_broad_full['biosample_term_name'] == cell_name)
        & (enc_broad_full['experiment_target'] == 'H3K36me3-human')
        ]

    # Found on promoters of actively transcribed genes
    hm_4_proms_0 = enc_broad_full[
        (enc_broad_full['assay'] == 'ChIP-seq')
        & (enc_broad_full['biosample_term_name'] == cell_name)
        & ((enc_broad_full['experiment_target'] == 'H3K4me3-human')
           | (enc_broad_full['experiment_target'] == 'H3K9ac-human'))
        ]
    hm_4_proms = hm_4_proms_0.cover(1, 'ANY')

    # Found on active enhancers - < 10000k from target genes
    hm_4_enhcrs = enc_broad_full[
        (enc_broad_full['assay'] == 'ChIP-seq')
        & (enc_broad_full['biosample_term_name'] == cell_name)
        & (enc_broad_full['experiment_target'] == 'H3K4me1-human')
        ]
    
    # print('# Extract narrowpeaks.')
    hepg2_narrow_df_list = []
    for tf in list_of_targets:
        hepg2_narrow_df_list.append(
            enc_narrow_full[(enc_narrow_full[
                                 'biosample_term_name'] == cell_name)
                            & (enc_narrow_full['assay'] == 'ChIP-seq')
                            & (
                                enc_narrow_full['experiment_target'] == tf)])
    hepg2_narrow_data = hepg2_narrow_df_list[0]
    print(hepg2_narrow_data.materialize().regs)
    for df in hepg2_narrow_df_list[1:]:
        hepg2_narrow_data = hepg2_narrow_data.union(df)

    # hepg2_narrow_data = enc_narrow_full[
    #     (enc_narrow_full['biosample_term_name'] == CELL_NAME)
    #     & (enc_narrow_full['assay'] == 'ChIP-seq')
    # ]
    npeaks = hepg2_narrow_data.reg_project(
        new_field_dict={
            'start': hepg2_narrow_data.start + hepg2_narrow_data.peak,
            'stop': hepg2_narrow_data.start + hepg2_narrow_data.peak + 1}
    )

    merged_npeaks = npeaks.merge()
    print(len(merged_npeaks.materialize().regs))
    exit()
    strands = ['+', '-']  # To streamline the code

    results = []
    for this_strand in strands:
        # Extract only TSS on the strand in context for computation
        raw_tsses = tss_full.reg_select(tss_full.strand == this_strand)

        # print('# First extensions: to exon size.')
        if this_strand == '+':
            exons = raw_tsses.reg_project(
                new_field_dict={'stop': raw_tsses.stop + exon_length}
            )
        else:
            exons = raw_tsses.reg_project(
                new_field_dict={'start': raw_tsses.start - exon_length}
            )
        exons_on_hms = exons.map(hm_4_exons,
                                 refName='exons', expName='hm_4_exons')
    
        f_exons = exons_on_hms.reg_select(
            exons_on_hms.count_exons_hm_4_exons != 0
        )
        # print('# Second extensions: to promoter size.')
        if this_strand == '+':
            promoters = f_exons.reg_project(
                new_field_dict={'start': f_exons.start - promoter_length}
            )
        else:
            promoters = f_exons.reg_project(
                new_field_dict={'stop': f_exons.stop + promoter_length}
            )
        promoters_on_hms = promoters.map(hm_4_proms,
                                         refName='promoters',
                                         expName='hm_4_proms')
        # Filtering via SELECT
        f_promoters = promoters_on_hms.reg_select(
            promoters_on_hms.count_promoters_hm_4_proms != 0
        )

        # print('# Third extensions: to enhancer size.')
        # why do we consider them to be honest?
        if this_strand == '+':
            enhancers = f_promoters.reg_project(
                new_field_dict={'start': f_promoters.start - enhancer_length}
            )
        else:
            enhancers = f_promoters.reg_project(
                new_field_dict={'stop': f_promoters.stop + enhancer_length}
            )
        enhancers_on_hms = enhancers.map(hm_4_enhcrs,
                                         refName='enhancers',
                                         expName='hm_4_enhcrs')
        # Filtering via SELECT
        f_enhancers = enhancers_on_hms.reg_select(
            enhancers_on_hms.count_enhancers_hm_4_enhcrs != 0
        )

        # print('# Return to promoter size.')
        if this_strand == '+':
            f_new_promoters = f_enhancers.reg_project(
                new_field_dict={'start': f_promoters.start + enhancer_length
                                         - promoter_length}
            )
        else:
            f_new_promoters = f_enhancers.reg_project(
                new_field_dict={'stop': f_promoters.stop - enhancer_length
                                        + promoter_length}
            )


        # print('# Map promoters on narrowpeaks.')
        mapped_promoters = f_new_promoters.map(merged_npeaks,
                                               refName='f_new_promoters',
                                               expName='merged_peaks')
        # Filtering via SELECT
        f_mapped_promoters = mapped_promoters.reg_select(
            mapped_promoters.count_f_new_promoters_merged_peaks >= min_tfbs_count
        )
        print(len(f_mapped_promoters.materialize().regs))
        # Go back to 1bp size
        if this_strand == '+':
            mapped_tsses = f_mapped_promoters.reg_project(
                new_field_dict={
                    'start': mapped_promoters.start + promoter_length,
                    'stop': mapped_promoters.stop - exon_length}
            )
        else:
            mapped_tsses = f_mapped_promoters.reg_project(
                new_field_dict={'start': mapped_promoters.start - exon_length,
                                'stop': mapped_promoters.stop
                                        + promoter_length}
            )
        results.append(mapped_tsses)  # For clarity
        # Strand completed

    both_strands_res_0 = results[0].union(results[1]).merge()
    both_strands_res = both_strands_res_0.materialize()
    # for testing purposes
    try:
        both_strands_res_0.materialize(output_path=OUTFILE_PATH)
    except IndexError:
        pass
    return both_strands_res


def compute_nulls(i_cell='HepG2'):  # +a list of parameters
    """Computes the mindistance couple distance distributions given
    two TFBS datasets and returns a null table Model row for
    insertion.

    Keyword arguments:
        -- ds1, ds2: GMQLDatasets containing binding sites for each TF
        and maps to TSS
        -- use_tsses: defines whether the algorithm should search for
        colocation in promoters. Use False for null distributions.
        (default: True)"""
    # TODO make this list reading from database
    # SP: I'm adding two input parameters, cell and a tf_list. For now
    # I don't use them but we should use them in the above TODO
    if not 'calculate_null-' + i_cell in STATIC_CACHE:
        def calc():
            # TODO make this list reading from database
            include_list = list(
                CellLineTfs.objects.filter(cell_line=i_cell).filter(use_in_null=True).values_list('tf', flat=True))

            nullpd = pd.DataFrame(list(CellLineNull.objects.filter(cell_line=i_cell).filter(tf1__in=include_list)
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

        STATIC_CACHE['calculate_null-' + i_cell] = calc()
    return STATIC_CACHE['calculate_null-' + i_cell]

# User-guided workflow-only
def __get_tf_list__(cell):
    """Ancillary function to check_tfs. Returns the list of all
    available tfs in a cell line. If cell is "user", instead returns
    the list of TFs provided by the user in the current session."""
    # We need to optimize this
    return CellLineTfs.objects.filter(cell_line=cell).values_list(
        'tf', flat=True)

def output_results(candidate, input_cell, max_distance=2200,
                   tail_size=1000,min_tss=0.01,
                   min_count=1,p_value=0.2,
                   min_num_true_test=3,
                   test_list=('average', 'mad', 'median', 'tail_1000')):
    """Checks whether a candidate passes the TICA workflow tests
    and returns result and distance distribution graph.
    Keyword arguments:
        -- Model: table row containing statistics for the candidate
    """
    # lazy val
    all_tfs = sorted(list(__get_tf_list__()))
    calculated_null = compute_nulls(i_cell=input_cell)
    temp_null = calculated_null[max_distance]
    
    result = []
    for tf in all_tfs:
        if tf == candidate:
            continue
        tf1 = candidate
        tf2 = tf
        if tf1 > tf2:
            tf1 = tf
            tf2 = candidate
        # print(tf1)
        # print(tf2)

        # contains the max line less then or equal to maxd
        # TODO we can select all together, this will be faster
        line = CellLineCouple.objects.filter(tf1=tf1).filter(tf2=tf2).filter(
            distance__lte=max_distance).order_by('-distance').first()
        # why??
        line_null = Hepg2Null.objects.filter(tf1=tf1).filter(tf2=tf2).filter(
            max_distance=max_distance).values().first()

        if line is None:
            continue

        if line.cumulative_count_all < min_count:
            continue

        if line.cumulative_count_tss/line.cumulative_count_all < min_tss:
            continue

        # start stat testing
        passed = []
        scores = {}
        for i in test_list:
            test_name = i + "-" + str(p_value)
            null_value = temp_null[test_name]
            if line_null[i] is None:
                continue
            # TODO check correctness
            if line_null[i] <= null_value:
                passed.append(i)
            scores[i] = line_null[i]
        if min_num_true_test <= len(passed):
            scores['name'] = tf
            result.append(scores)

    # result is list of tuples first element is name of tf
    # and second one is passed test
    return result