from tester.pipeline_steps import *
from tester.min_dist import *

from django.db import connections


def pipeline_controller(session_id, method='', cell=''):
    try:
        res = MyDataEncodeFormModel.objects.filter(session_id=session_id).first()


        input_zip = res.mydata.path
        tss_file = 'media/active_tsses.bed'
        temp_folder = 'media/temp/%s/' % session_id

        # connections.close_all()

        tfs = data_uploader(input_zip, target_folder='%s/test2/' % temp_folder)
        your_data = pygmql.load_from_path(
            local_path='%s/test2/' % temp_folder,
            parser=pygmql.parsers.NarrowPeakParser())
        your_data.materialize('%s/gatto_banane-2/' % temp_folder)
        your_signals = tfbs_filter(your_data, tfs)
        # tfs are scrambled
        your_signals.materialize('%s/new_test_attempt_2/' % temp_folder)
        materialized_files = ['%s/new_test_attempt_2/exp/%s' % (temp_folder, item)
                              for item in list(os.walk('%s/new_test_attempt_2/' % temp_folder))[-1][2]
                              if not item.startswith('.')
                              and not item.startswith('_')
                              and '.meta' not in item
                              and '.schema' not in item]
        tfs = [list(map(lambda s: s.strip().split('\t')[1], open('%s/new_test_attempt_2/exp/%s' % (temp_folder, item), 'r')))[0]
               for item in list(os.walk('%s/new_test_attempt_2/' % temp_folder))[-1][2]
               if not item.startswith('.')
               and '.meta' in item]
        print(tfs)
        os.makedirs('%s/ciao/' % temp_folder, exist_ok=True)
        your_maps = tfbs2tss_mapper(materialized_files, tfs, tss_file,
                                    target_folder='%s/ciao/' % temp_folder)

        compute_min_distance(session_id, '%s/ciao/' % temp_folder, '%s/ciao/' % temp_folder, 2200)

        print("\n\n\n\n\n\nchild\n\n\n\n\n", res.session_id, type(res), session_id, "\n\n\n\n\n\nchild\n\n\n\n\n")
    except Exception as e:
        print(e)
    finally:
        print("finally")
        connections.close_all()
        os._exit(0)
