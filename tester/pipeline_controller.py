from django.db import connections

from tester.min_dist import compute_min_distance
from tester.models import MyDataEncodeFormModel
from tester.pipeline_steps import *
import logging


def pipeline_controller(session_id, method='', cell=''):
    try:
        res = MyDataEncodeFormModel.objects.filter(session_id=session_id).first()

        max_distance = res.max_dist

        input_zip = res.mydata.path
        tss_file = 'media/active_tsses.bed'
        temp_folder = 'media/temp/%s/' % session_id


        # connections.close_all()

        unzipped_folder = '%s/unzipped/' % temp_folder
        tfbs_folder = '%s/tfbs/' % temp_folder
        tfbs_to_tss_maps_folder = '%s/tfbs_to_tss_maps/' % temp_folder

        tfs = data_uploader(input_zip, target_folder=unzipped_folder)

        your_data = pygmql.load_from_path(
            local_path=unzipped_folder,
            parser=pygmql.parsers.NarrowPeakParser())
        # your_data.materialize('%s/gatto_banane-2/' % temp_folder)
        your_signals = tfbs_filter(your_data, tfs)
        # tfs are scrambled
        your_signals.materialize(tfbs_folder)
        materialized_files = ['%s/exp/%s' % (tfbs_folder, item)
                              for item in list(os.walk(tfbs_folder))[-1][2]
                              if not item.startswith('.')
                              and not item.startswith('_')
                              and '.meta' not in item
                              and '.schema' not in item]
        tfs = [list(map(lambda s: s.strip().split('\t')[1], open('%s/exp/%s' % (tfbs_folder, item), 'r')))[0]
               for item in list(os.walk(tfbs_folder))[-1][2]
               if not item.startswith('.')
               and '.meta' in item]
        print(tfs)
        os.makedirs(tfbs_to_tss_maps_folder, exist_ok=True)
        your_maps = tfbs2tss_mapper(materialized_files, tfs, tss_file,
                                    target_folder=tfbs_to_tss_maps_folder)

        compute_min_distance(session_id, tfbs_to_tss_maps_folder, tfbs_to_tss_maps_folder, max_distance)

        print("\n\n\n\n\n\nchild\n\n\n\n\n", res.session_id, type(res), session_id, "\n\n\n\n\n\nchild\n\n\n\n\n")
    except Exception as e:
        logging.exception("Something awful happened!")
    finally:
        print("finally")
        connections.close_all()
        os._exit(0)
