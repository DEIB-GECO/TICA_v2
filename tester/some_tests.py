"""The summary line may be used by automatic indexing tools; it is 
important that it fits on one line and is separated from the rest 
of the docstring by a blank line. The summary line may be on the 
same line as the opening quotes or on the next line. 
The entire docstring is indented the same as the quotes at its first
line (see examples).

The docstring of a script (a stand-alone program) should be usable 
as its "usage" message, printed when the script is invoked with 
incorrect or missing arguments (or perhaps with a "-h" option, for 
"help"). Such a docstring should document the script's function and 
command line syntax, environment variables, and files. Usage 
messages can be fairly elaborate (several screens full) and should 
be sufficient for a new user to use the command properly, as well 
as a complete quick reference to all options and arguments for the 
sophisticated user.

The docstring for a module should generally list the classes, 
exceptions and functions (and any other objects) that are exported 
by the module, with a one-line summary of each. (These summaries 
generally give less detail than the summary line in the object's 
docstring.) The docstring for a package (i.e., the docstring of 
the package's __init__.py module) should also list the modules and 
subpackages exported by the package.

The docstring for a function or method should summarize its 
behavior and document its arguments, return value(s), side effects, 
exceptions raised, and restrictions on when it can be called (all 
if applicable). Optional arguments should be indicated. It should 
be documented whether keyword arguments are part of the interface.

The docstring for a class should summarize its behavior and list 
the public methods and instance variables. If the class is 
intended to be subclassed, and has an additional interface for 
subclasses, this interface should be listed separately (in the 
docstring). The class constructor should be documented in the 
docstring for its __init__ method. Individual methods should be 
documented by their own docstring.

If a class subclasses another class and its behavior is mostly 
inherited from that class, its docstring should mention this and 
summarize the differences. Use the verb "override" to indicate 
that a subclass method replaces a superclass method and does not 
call the superclass method; use the verb "extend" to indicate that 
a subclass method calls the superclass method (in addition to its 
own behavior).

    Keyword arguments:
    arg1 -- first argument (default def_value1)
    arg2 -- second argument  (default def_value2)

DEPENDENCIES:
List of parent or related scripts together with their content and
connection with current script
    * Script1Name: Description
    * Script2Name: Description

CONFIGURATION VARIABLES:
List of variable to be passed to the script using a configuration
file,with their use and any restriction, if applicable
    [Section1]
    * Var1Name: Description
    * Var2Name: Description
    
    [Section2]
    * Var1Name: Description
    * Var2Name: Description

OUTPUT:
List of effects and output variables produced by successful script
execution
    * Effect1: Description;
    * Var1Name: Description;

Author: Stefano Perna (stefano.perna@polimi.it)
Date: date of construction
Version: version name"""
import sys
import pipeline_steps
import gmql as pygmql
import os

# def pipp():
#     bananetf = tester.pipeline_steps.data_uploader('tester/arif.zip',
#                                                    'test_banane/')
#     print(bananetf)
#     exit()
#
# pipp()
# exit()
NARROW_PATH = '/Volumes/PERNA/ENC_narrow_Aug_2017/'
TEST_DATA = '/Volumes/PERNA/ENCODE_data_4_tests/'

# CELL_NAME = 'HepG2'
#
# # Temporary for debugging
# list_of_targets = sorted(['JUN-human', 'ATF3-human', 'MYC-human'])
#
# # with open(TF_LIST_PATH, 'r') as tf_list_file:
# #     list_of_targets = sorted(map(lambda s: s.strip(), tf_list_file))
#
# enc_narrow_full = pygmql.load_from_path(
#     local_path=NARROW_PATH,
#     parser=pygmql.parsers.NarrowPeakParser())
#
# print('after loading')
# datasets = []
# tf_list = set([])
# for index, tf in enumerate(list_of_targets):
#     this_ds = enc_narrow_full[
#         (enc_narrow_full['biosample_term_name'] == CELL_NAME)
#         & (enc_narrow_full['assay'] == 'ChIP-seq')
#         & (enc_narrow_full['experiment_target'] == tf)
#     ]
#     #].materialize()  # Available in future versions?
#     datasets.append(this_ds)
#     # tf_list = tf_list.union(set([item[0] for item in this_ds.meta[
#     #     'experiment_target'].values])
#     #                         )
#
# # test = enc_narrow_full[
# #         (enc_narrow_full['biosample_term_name'] == CELL_NAME)
# #         & (enc_narrow_full['assay'] == 'ChIP-seq')
# #         & (enc_narrow_full['experiment_target'] == 'MYC-human')].materialize()
# # print(len(test.regs))
# # exit()
# # # Have to materialize first?
# # test_data = pipeline_steps.tfbs_filter(
# #     datasets, list_of_targets
# # )
# # test_data.materialize(output_path='20-Oct-2017')
# print('I got here')
# tmp = tester.pipeline_steps.tss_filter('/Volumes/PERNA/TSSes/',
#                                 cell_name='HepG2',
#                                 list_of_targets='JUN-human')
# print('I also got here.')
# print(tmp.regs)


# ## ALGORITHMIC WORKFLOW
#

# tmp = test_ds.materialize()
# print(tmp.meta['experiment_target'].values)
# tfs = sorted(list(set(tmp.meta['experiment_target'].values)))


# enc_narrow_full = pygmql.load_from_path(
#     local_path=NARROW_PATH,
#     parser=pygmql.parsers.NarrowPeakParser())
# test = enc_narrow_full[
#         (enc_narrow_full['biosample_term_name'] == 'HepG2')
#         & (enc_narrow_full['assay'] == 'ChIP-seq')
#         & (enc_narrow_full['experiment_target'] == 'MYC-human')].materialize()
# print(test.meta)
# test2 = test.to_GMQLDataset()
# file2 = test2.materialize()
# print(file2.meta)
# exit()

#print(tfs)
## USER-GUIDED WORKFLOW

input_zip = 'test2.zip'
cell_line = 'HepG2'
tss_file = 'active_tsses.bed'
tfs = pipeline_steps.data_uploader(input_zip, target_folder='test2/')
your_data = pygmql.load_from_path(
    local_path='test2/',
    parser=pygmql.parsers.NarrowPeakParser())
your_data.materialize('gatto_banane-2/')
your_signals = pipeline_steps.tfbs_filter(your_data, tfs)
# tfs are scrambled
your_signals.materialize('new_test_attempt_2/')
materialized_files = ['new_test_attempt_2/exp/%s' % item
                      for item in list(os.walk('new_test_attempt_2/'))[-1][2]
                      if not item.startswith('.')
                      and not item.startswith('_')
                      and '.meta' not in item
                      and '.schema' not in item]
tfs = [list(map(lambda s: s.strip().split('\t')[1], open('new_test_attempt_2/exp/%s' % item, 'r')))[0]
                      for item in list(os.walk('new_test_attempt_2/'))[-1][2]
                      if not item.startswith('.')
                      and '.meta' in item]
print(tfs)
your_maps = pipeline_steps.tfbs2tss_mapper(materialized_files, tfs, tss_file,
                                           target_folder='ciao/')

pipeline_steps.compute_mindist('ciao/','HepG2',2200)
