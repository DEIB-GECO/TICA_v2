"""Contains the three controllers that manage the execution of the
TICAv2 workflow.

data_uploader() takes a file list, accesses the server position
and loads datasets, returning them to the workflow(s).

UD_filter() is run every time the user uploads data to use with
TICA. It filters user defined data according to parameters and returns
a dataframe to use with TICA algorithms. It also maps provided binding
sites to the TSSes of the context cell line.

TFBS_2_TSS_mapper() runs every time that TFBSes and/or TSSes are
filtered. Maps TFBS to TSSes according to their IDs.

ALG_controller() run the main TICA algorithm. It uses auxilliary
functions from utils.py. Return test metrics and test results
for the django app "tester".


Author: Stefano Perna (stefano.perna@polimi.it)
Date: 18 October 2017
Version: 0.1"""
import sys
import utils


# Common functions
def data_uploader(file_list):
    """Loads datasets from the disk returns formatted GMQLDatasets.
    Keyword arguments:
        -- file_list: list of files to be accessed on disk
    """
    return GMQLDatasets


def tfbs_filter(datasets, min_acc_value=3):
    """Filters binding sites according to accumulation values in the
    moving window.
    Keyword arguments:
        -- datasets: GMQLDatasets containing TFBSes
        -- min_acc_value: minimum number of TFBSes from the same TFs
        to be found in the moving window (default: 3)
    """
    return GMQLDatasets


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
def tss_filter(tss_file_path, min_tfbs_count=50):
    """Filters transcription start sites according to the presence of
    histone marks and the count of TFBS from the same cell line found
    in the promoter of each TSS.
    Keyword arguments:
        -- tss_file_path: path to tss file for loading
        -- min_tfbs_count: minimum number of TFBSes from the same cell
        to be found in the promoter of a valid TSS (default: 50)
    """
    return GMQLDatasets


# User-guided workflow-only
def output_results(Model):
    """Checks whether a candidate passes the TICA workflow tests
    and returns result and distance distribution graph.
    Keyword arguments:
        -- Model: table row containing statistics for the candidate
    """
    return GMQLDatasets