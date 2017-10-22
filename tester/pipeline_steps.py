"""Contains the pipeline chuncks which are used by the controller to
 manage the TICA workflow. Please refer to each function for a
 description.
 
NOTE: this script require the existance of one metadata attribute
'TF_name' in all input datasets, which contains the gene symbol of the
TF which they contain.

Author: Stefano Perna (stefano.perna@polimi.it)
Date: 18 October 2017
Version: 0.1"""
import sys
#import utils
import gmql as pygmql
import copy
import tqdm as timer


# Common functions
def data_uploader(file_list):
    """Loads datasets from the disk returns formatted GMQLDatasets.
    Keyword arguments:
        -- file_list: list of files to be accessed on disk
    """
    return GMQLDatasets


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
    
    ds_list = []

    for index in range(len(tf_list)):
        ds_list.append(datasets[index].to_GMQLDataset())
    
    # First process the simple ones in batch
    tfbs_data = ds_list[0]
    for df in ds_list[1:]:
        tfbs_data = tfbs_data.union(df)
    
    print(tfbs_data.materialize().meta)
    exit()
    # NOTE: we assume to be already in 1bp length form after upload
    # npeaks = tfbs_data.reg_project(
    #     new_field_dict={
    #         'start': hepg2_narrow_data.start + hepg2_narrow_data.peak,
    #         'stop': hepg2_narrow_data.start
    #                 + hepg2_narrow_data.peak + 1}
    # )

    # NOTE: groupBy must be given in list format
    covered = tfbs_data.cover(1, 'ANY', groupBy=['experiment_target'])

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


def tfbs2tss_mapper(datasets, tss_dataset, target_folder='path/to/default'):
    """Maps TFBSes to promoters of TSSes using IDs. Stores maps as
    comma-separated-values on disk and returns them as dicts (?).
    Keyword arguments:
        -- datasets: GMQLDatasets containing TFBSes
        -- tss_dataset: GMQLDataset containing TSSes
        -- target_folder: folder where TFBS_to_TSS maps will be stored
        (default: 'path/to/default')
    """
    return dict


def compute_mindistances(ds1, ds2, use_tsses=True):  # +a list of parameters
    """Computes the mindistance couple distance distributions given
    two TFBS datasets and returns a null table Model row for
    insertion.
    
    Keyword arguments:
        -- ds1, ds2: GMQLDatasets containing binding sites for each TF
        and maps to TSS
        -- use_tsses: defines whether the algorithm should search for
        colocation in promoters. Use False for null distributions.
        (default: True)"""
    
    return # A model for the appropriate table


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
    #OUTFILE_PATH = 'test_2/'


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

        # print('# Map promoters on narrowpeaks.')
        mapped_promoters = f_new_promoters.map(merged_npeaks,
                                               refName='f_new_promoters',
                                               expName='merged_peaks')
        # Filtering via SELECT
        f_mapped_promoters = mapped_promoters.reg_select(
            mapped_promoters.count_f_new_promoters_merged_peaks >= min_tfbs_count
        )
    
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


# User-guided workflow-only
def output_results(Model):
    """Checks whether a candidate passes the TICA workflow tests
    and returns result and distance distribution graph.
    Keyword arguments:
        -- Model: table row containing statistics for the candidate
    """
    return GMQLDatasets