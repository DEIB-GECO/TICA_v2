from django.db import connections

from tester.min_dist import compute_min_distance
from tester.models import MyDataEncodeFormModel
from tester.pipeline_steps import *
import logging
import datetime


def pipeline_controller(session_id, method='mydata_mydata', cell=''):
    try:
        res = MyDataEncodeFormModel.objects.filter(session_id=session_id).first()

        input_zip = res.mydata.path
        encode_folder = 'media/encode/%s/' % cell
        tss_file = 'media/encode/tss/%s.gdm' % cell
        temp_folder = 'media/temp/%s/' % session_id
        os.makedirs(temp_folder)

        timefile = open('%s/mytimings.txt' % temp_folder, 'w')

        # connections.close_all()

        unzipped_folder = '%s/unzipped/' % temp_folder
        tfbs_folder = '%s/tfbs/' % temp_folder
        tfbs_to_tss_maps_folder = '%s/tfbs_to_tss_maps/' % temp_folder

        tfs = data_uploader(input_zip, target_folder=unzipped_folder)

        pre_time = datetime.datetime.now()
        # timefile.write('PROCESS_START;%s\n' % datetime.datetime.now().time())
        your_data = pygmql.load_from_path(
            local_path=unzipped_folder,
            parser=pygmql.parsers.NarrowPeakParser())
        # your_data.materialize('%s/gatto_banane-2/' % temp_folder)
        your_signals = tfbs_filter(your_data, tfs)
        # tfs are scrambled
        your_signals.materialize(tfbs_folder)
        timefile.write('TFBS_Q_DONE: %s min\n' % ((datetime.datetime.now() - pre_time).total_seconds() / 60))
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

        pre_time = datetime.datetime.now()
        your_maps = tfbs2tss_mapper(materialized_files, tfs, tss_file,
                                    target_folder=tfbs_to_tss_maps_folder)
        timefile.write('MAPS_DONE: %s min\n' % ((datetime.datetime.now() - pre_time).total_seconds() / 60))

        pre_time = datetime.datetime.now()
        if method == 'mydata_mydata':
            compute_min_distance(session_id, tfbs_to_tss_maps_folder, tfbs_to_tss_maps_folder)
        else:
            compute_min_distance(session_id, tfbs_to_tss_maps_folder, encode_folder)
        timefile.write('MINDIST_DONE: %s min\n' % ((datetime.datetime.now() - pre_time).total_seconds() / 60))
        timefile.close()

        res.upload_status = "SUCCESS"
        res.save()

        print("\n\n\n\n\n\nchild\n\n\n\n\n", res.session_id, type(res), session_id, "\n\n\n\n\n\nchild\n\n\n\n\n")
    except Exception as e:
        res.upload_status = "FAIL"
        res.save()
        logging.exception("Something awful happened!")
    finally:
        print("finally")
        connections.close_all()
        os._exit(0)
