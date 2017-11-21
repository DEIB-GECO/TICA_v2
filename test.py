import pandas as pd
import os
import intervaltree as it
import numpy as np
from tester.pipeline_steps import tfbs2tss_mapper
from tester.models import CellLineTfs
CHRS = list(map(lambda x: "chr" + str(x), range(1, 23))) + ["chrX"]


def update_encode(cell_line="banane", tfbs_files_path='example/', tss_file_path='example/tss/gm12878.gdm'):
    files = list(zip(*map(lambda x: (x, os.path.join(tfbs_files_path, x)), next(os.walk(tfbs_files_path))[2])))
    
    #print(files)
    tfs = list(map(lambda s: s.replace('.gdm', ''), files[0]))
    filesizes = list(map(lambda f: os.stat(f).st_size, files[1]))
    upper = np.percentile(filesizes, q=90, interpolation='higher')
    lower = np.percentile(filesizes, q=10, interpolation='lower')
    null_flags = list(map(lambda value: lower < value < upper, filesizes))
    for index in range(len(tfs)):
        new_result = CellLineTfs(cell_line=cell_line, tf=tfs[index],
                                 use_in_null=null_flags[index])
        new_result.save()
    temp_folder = 'media/encode/%s/' % cell_line
    tfbs2tss_mapper(
        files[1],
        files[0],
        tss_file_path,
        temp_folder
    )
    from tester.min_dist import compute_min_distance

    compute_min_distance("ENCODE_%s" % cell_line, temp_folder, temp_folder)