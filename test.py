import pandas as pd
import os
import intervaltree as it
from tester.pipeline_steps import tfbs2tss_mapper

CHRS = list(map(lambda x: "chr" + str(x), range(1, 23))) + ["chrX"]





def run(cell_line="hepg2_4", tfbs_files_path='media/temp/127_0_0_1_1510848168_4206731//tfbs/', tss_file_path='media/tss/gm12878.gdm'):
    files = list(zip(*map(lambda x: (x, os.path.join(tfbs_files_path, x)), next(os.walk(tfbs_files_path))[2])))

    temp_folder = 'media/encode/%s/' % cell_line

    tfbs2tss_mapper(
        files[1],
        files[0],
        tss_file_path,
        temp_folder
    )
    from tester.min_dist import compute_min_distance

    compute_min_distance("ENCODE_%s" % cell_line, temp_folder, temp_folder)
