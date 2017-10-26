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

import multiprocessing
import statistics
from collections import defaultdict
from multiprocessing import Lock, Process
from queue import Empty

# Chromosome names
CHRS = list(map(lambda x: "chr" + str(x), range(1, 23))) + ["chrX"]
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
                    [item for item in files if not item.startswith('.')
                     and '.meta' not in item]
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


def tfbs_filter(tfbs_data, tf_list, window_size=1000, min_acc_value=3):
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
    
    # # First process the simple ones in batch
    # tfbs_data = datasets[0]
    # for df in datasets[1:]:
    #     tfbs_data = tfbs_data.union(df)
    
    tfbs_data.materialize('input_banane-1/')
    npeaks = tfbs_data.reg_project(
        new_field_dict={
            'start': tfbs_data.start + tfbs_data.peak,
            'stop': tfbs_data.start + tfbs_data.peak + 1}
    )
    npeaks.materialize('npeaks_banane0/')
    # NOTE: groupBy must be given in list format
    covered = npeaks.cover(1, 'ANY', groupBy=['experiment_target'])
    covered.materialize('cover_banane1/')
    signals = covered # Is it the same as copying?
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


def compute_mindist(target_directory='ciao/',
                    i_cell='HepG2', max_distance=2200):  # +a list of parameters
    """Computes the min_distance couple distance distributions given
    two TFBS datasets and returns a null table Model row for
    insertion.

    Keyword arguments:
        -- ds1, ds2: GMQLDatasets containing binding sites for each TF
        and maps to TSS
        -- use_tsses: defines whether the algorithm should search for
        colocation in promoters. Use False for null distributions.
        (default: True)"""
    # definitions

    #max_distance = 2200

    # TODO remove
    result_file = "results/result_file_par.txt"
    result_file_merged = "results/result_file_merged_par.txt"

    infinity = max_distance * 100 - 1

    # list of chromosome
    chromosome_list = ["chr" + str(i + 1) for i in range(22)] + ["chrx"]

    # class definitions
    class Region(object):
        __slots__ = ['position', 'tss_set']
    
        def __init__(self, position, tss_list=None):
            self.position = position
            self.tss_set = tss_list
    
        def __str__(self):
            return str(self.position) + " " + str(self.tss_set)
    
        def __repr__(self):
            return str(self)

    # class definitions
    class TempRegion(object):
        __slots__ = ['list_id', 'position', 'tss_set']
    
        def __init__(self, tf, position, tss_list=None):
            self.list_id = tf
            self.position = position
            self.tss_set = tss_list
    
        def __str__(self):
            return self.list_id + " " + str(self.position) + " " + str(
                self.tss_set)
    
        def __repr__(self):
            return str(self)

    class Distance(object):
        __slots__ = ['distance', 'intersect_tss_list']
    
        def __init__(self, distance, intersect_tss_list=None):
            self.distance = distance
            self.intersect_tss_list = intersect_tss_list
    
        def __str__(self):
            return str(self.distance) + " " + str(self.intersect_tss_list)
    
        def __repr__(self):
            return str(self)

    def add_list_id(list, list_val):
        list = iter(list)
        while True:
            try:
                value = next(list)
                yield TempRegion(list_val, value.position, value.tss_set)
            except StopIteration:
                return

    # list1 and list2(ordered) are the same chromosome list of two TFs and returns ordered list
    def linear_merge(list1, list2):
        # return merged list, if not any of them empty otherwise return empty
        list1 = iter(add_list_id(list1, 'list1'))
        list2 = iter(add_list_id(list2, 'list2'))
    
        # if one of them is empty, then return nothing, this is easy for TICA application
        try:
            value1 = next(list1)
        except StopIteration:
            return
    
        try:
            value2 = next(list2)
        except StopIteration:
            return
    
        # We'll normally exit this loop from a next() call raising StopIteration, which is
        # how a generator function exits anyway.
        while True:
            if value1.position <= value2.position:
                # Yield the lower value.
                yield value1
                try:
                    # Grab the next value from list1.
                    value1 = next(list1)
                except StopIteration:
                    # list1 is empty.  Yield the last value we received from list2, then
                    # yield the rest of list2.
                    yield value2
                    while True:
                        try:
                            yield next(list2)
                        except StopIteration:
                            return
            else:
                yield value2
                try:
                    value2 = next(list2)
            
                except StopIteration:
                    # list2 is empty.
                    yield value1
                    while True:
                        try:
                            yield next(list1)
                        except StopIteration:
                            return

    # list1 and list2(ordered) are the same chromosome list of two TFs and returns the distance between the regions
    def linear_merge_distance(list1, list2):
        list_iter = iter(linear_merge(list1, list2))
        # set a pre region with name NO_TF at the position minus infinity
        region_pre = TempRegion("NO_LIST", -infinity)
        # send an infinity in the beginning
        yield Distance(infinity)
    
        while True:
            try:
                region_curr = next(list_iter)
                if region_curr.list_id == region_pre.list_id:
                    yield Distance(infinity)
                else:
                    yield Distance(region_curr.position - region_pre.position,
                                   None if region_pre.tss_set is None or region_curr.tss_set is None else region_curr.tss_set.intersection(
                                       region_pre.tss_set))
            
                region_pre = region_curr
            except StopIteration:
                # send an infinity at the end
                yield Distance(infinity)
                return

    lock = Lock()

    list_of_tf = []

    for (dir_path, dir_names, file_names) in os.walk(target_directory):
        list_of_tf.extend(file_names)
        break

    print("List of tfs:", list_of_tf)

    def read(tf):
        temp_tf = defaultdict(list)
        for line in open(target_directory + tf):
            s = line.strip().split("\t")
            # TODO change location
            tss_val = s[2] if len(s) > 2 else None
            tss_val = tss_val if tss_val != '-1' else None
            tss = set(
                [int(t) for t in tss_val.split(",")]) if tss_val else None
            c = s[0].lower()
            temp_tf[c].append(Region(int(s[1]), tss))
        temp_tf2 = dict()
        # Select only in chromosome list
        for key in chromosome_list:
            temp_tf2[key] = sorted(temp_tf[key], key=lambda x: x.position)
        return temp_tf2

    def get_tfs(tf, tfs):
        if tf not in tfs:
            tfs[tf] = read(tf)
        return tfs[tf]

    def calculate_distances(inp, tfs):
        (tf1, tf2) = inp
        temp_count_all = defaultdict(int)
        temp_count_tss = defaultdict(int)
    
        count_tss = 0
    
        distances = []
    
        tf1r_dict = get_tfs(tf1, tfs)
        tf2r_dict = get_tfs(tf2, tfs)
        # out_file = open("results2/" + tf1 + "-" + tf2 + ".txt", "w")
    
        for c in chromosome_list:
            tf1r = tf1r_dict[c]
            tf2r = tf2r_dict[c]
        
            merged_distances = linear_merge_distance(tf1r, tf2r)
            pre_distance = next(merged_distances)
            curr_distance = next(merged_distances)
            for postDistance in merged_distances:
                if curr_distance.distance <= max_distance and curr_distance.distance <= pre_distance.distance and curr_distance.distance <= postDistance.distance:
                    # TODO remove
                    # out_file.write("\t".join([tf1, tf2, str(curr_distance.distance), str(int(bool(curr_distance.intersectTssList)))]) + "\n")
                    # out_file.flush()
                
                    temp_count_all[curr_distance.distance] += 1
                    distances.append(curr_distance.distance)
                    if curr_distance.intersect_tss_list:
                        temp_count_tss[curr_distance.distance] += 1
                        count_tss += 1
                pre_distance = curr_distance
                curr_distance = postDistance
    
        cumulative_count_all = 0
        cumulative_count_tss = 0
        with lock:
            for dist, count_all_temp in sorted(temp_count_all.items()):
                count_tss_temp = temp_count_tss[dist]
                cumulative_count_all += count_all_temp
                cumulative_count_tss += count_tss_temp
                out_file_merged.write("\t".join(
                    [tf1, tf2, str(dist), str(count_all_temp),
                     str(count_tss_temp), str(cumulative_count_all),
                     str(cumulative_count_tss)]) + "\n")
            out_file_merged.flush()
            # out_file.close()
        count_all = len(distances)
        if count_all > 0:
            mean = statistics.mean(distances)
            median = statistics.median(distances)
            mad = statistics.median([abs(x - median) for x in distances])
            tail1000 = len([x for x in distances if x >= 1000]) / count_all
        
            tails = []
            for i in range(11):  # TODO range(1,10)
                tails.append(len([x for x in distances if
                                  x >= max_distance * i / 10]) / count_all)
        
            # TODO other tails
        
            print(
            "RESULT:", tf1, tf2, max_distance, count_all, count_tss, mean,
            median, mad, tail1000, tails)

    out_file = open(result_file, "w")
    out_file_merged = open(result_file_merged, "w")

    class Consumer(multiprocessing.Process):
        def __init__(self, task_queue, result_queue):
            multiprocessing.Process.__init__(self)
            self.task_queue = task_queue
            self.result_queue = result_queue
    
        def run(self):
            tfs = dict()
            process_name = self.name
            print('%s' % process_name)
            while True:
                next_task = self.task_queue.get()
                if next_task is None:
                    # Poison pill means shutdown
                    print('%s: Exiting' % process_name)
                    self.task_queue.task_done()
                    break
                print('%s: %s' % (process_name, next_task))
                answer = next_task(tfs)
                self.task_queue.task_done()
                self.result_queue.put(answer)
            return

    class Task(object):
        def __init__(self, tf1, tf2):
            self.tf1 = tf1
            self.tf2 = tf2
    
        def __call__(self, tfs):
            calculate_distances((self.tf1, self.tf2), tfs)
            return '%s - %s' % (self.tf1, self.tf2)
    
        def __str__(self):
            return '%s - %s' % (self.tf1, self.tf2)

    if __name__ == '__main__':
        # Establish communication queues
        tasks = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()
    
        # Start consumers
        num_consumers = min(1, int(multiprocessing.cpu_count()))
        print('Creating %d consumers' % num_consumers)
        consumers = [Consumer(tasks, results) for i in range(num_consumers)]
        # consumers = [Consumer(tasks, results)]
    
        for w in consumers:
            w.start()
    
        # Enqueue jobs
        for (tf1, tf2) in [(tf1, tf2) for tf1 in list_of_tf for tf2 in
                           list_of_tf if tf1 < tf2]:
            tasks.put(Task(tf1, tf2))
        print("all tasks added")
    
        # Add a poison pill for each consumer
        for i in range(len(consumers)):
            tasks.put(None)
        print("all poisons added")
    
        count = 0
        # Start printing results
        while not tasks.empty():
            try:
                result = results.get(timeout=1)
                count += 1
                print('\t\t\tA Count: ', count, ' - Result:', result)
            except Empty:
                # print ('##timeout##')
                pass
        # Wait for all of the tasks to finish
        tasks.join()
    
        # Start printing results
        while not results.empty():
            result = results.get()
            count += 1
            print('\t\t\tB Count: ', count, ' - Result:', result)
    
        out_file_merged.close()
        out_file.close()

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