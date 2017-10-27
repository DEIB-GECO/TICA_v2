import multiprocessing
import statistics
from collections import defaultdict
from multiprocessing import Process
from os import walk
from queue import Empty

from tester.models import *

# definitions

infinity = 10000 * 100 - 1

# list of chromosome
chromosome_list = ["chr" + str(i + 1) for i in range(22)] + ["chrx"]

MAX_CPU = 8


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
        return self.list_id + " " + str(self.position) + " " + str(self.tss_set)

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
                yield Distance(region_curr.position - region_pre.position, None if region_pre.tss_set is None or region_curr.tss_set is None else region_curr.tss_set.intersection(region_pre.tss_set))

            region_pre = region_curr
        except StopIteration:
            # send an infinity at the end
            yield Distance(infinity)
            return


class Consumer(multiprocessing.Process):
    def __init__(self, task_queue, result_queue, session_id, max_distances, directory1, directory2):
        multiprocessing.Process.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.session_id = session_id
        self.max_distances = max_distances
        self.directory1 = directory1
        self.directory2 = directory2

    def run(self):
        tfs = dict()
        process_name = self.name
        # print('%s' % process_name)
        while True:
            next_task = self.task_queue.get()
            if next_task is None:
                # Poison pill means shutdown
                # print('%s: Exiting' % process_name)
                self.task_queue.task_done()
                break
            # print('%s: %s' % (process_name, next_task))
            answer = next_task(tfs, self.session_id, self.max_distances, self.directory1, self.directory2)
            self.task_queue.task_done()
            self.result_queue.put(answer)
        return


def read(tf, directory):
    # print("READ: ", target_directory + tf)
    temp_tf = defaultdict(list)
    for line in open(directory + tf):
        s = line.strip().split("\t")
        # TODO change location
        tss_val = s[2] if len(s) > 2 else None
        tss_val = tss_val if tss_val != '-1' else None
        tss = set([int(t) for t in tss_val.split(",")]) if tss_val else None
        c = s[0].lower()
        temp_tf[c].append(Region(int(s[1]), tss))
    temp_tf2 = dict()
    # Select only in chromosome list
    for key in chromosome_list:
        temp_tf2[key] = sorted(temp_tf[key], key=lambda x: x.position)
    return temp_tf2


def get_tfs(tf, tfs, directory):
    tf_id = "%s/%s" % (directory, tf)
    if tf_id not in tfs:
        tfs[tf_id] = read(tf, directory)
    return tfs[tf_id]


class Task(object):
    def __init__(self, tf1, tf2):
        self.tf1 = tf1
        self.tf2 = tf2

    def __call__(self, tfs, session_id, max_distances, directory1, directory2):
        self.session_id = session_id
        self.max_distances = max_distances
        self.target_directory1 = directory1
        self.target_directory2 = directory2

        return self.calculate_distances((self.tf1, self.tf2), tfs)

    def __str__(self):
        return '%s - %s' % (self.tf1, self.tf2)

    def calculate_distances(self, inp, tfs):
        (tf1, tf2) = inp

        max_distance = self.max_distances[0]

        # temp_count_all = defaultdict(int)
        # temp_count_tss = defaultdict(int)

        # count_tss = 0

        distances = []

        tf1r_dict = get_tfs(tf1, tfs, self.target_directory1)
        tf2r_dict = get_tfs(tf2, tfs, self.target_directory2)
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

                    distances.append((curr_distance.distance, bool(curr_distance.intersect_tss_list)))


                    # temp_count_all[curr_distance.distance] += 1
                    # if curr_distance.intersect_tss_list:
                    # temp_count_tss[curr_distance.distance] += 1
                    # count_tss += 1
                pre_distance = curr_distance
                curr_distance = postDistance

        cumulative_count_all = 0
        cumulative_count_tss = 0
        # with lock:
        #     for dist, count_all_temp in sorted(temp_count_all.items()):
        #         count_tss_temp = temp_count_tss[dist]
        #         cumulative_count_all += count_all_temp
        #         cumulative_count_tss += count_tss_temp
        #         out_file_merged.write("\t".join([tf1, tf2, str(dist), str(count_all_temp), str(count_tss_temp), str(cumulative_count_all), str(cumulative_count_tss)]) + "\n")
        #     out_file_merged.flush()
        # out_file.close()

        results = []
        for md in self.max_distances:
            if md != max_distance:
                distances = [dist for dist in distances if dist[0] <= md]

            res = dict()
            res['tf1'] = tf1
            res['tf2'] = tf2
            res['max_distance'] = md

            count_all = len(distances)
            count_tss = len([dist for dist in distances if dist[1]])
            distances_first_values = [dist[0] for dist in distances]
            res['count_all'] = count_all
            res['count_tss'] = count_tss

            if count_all > 0:
                res['average'] = statistics.mean(distances_first_values)
                res['median'] = statistics.median(distances_first_values)
                res['mad'] = statistics.median([abs(x - res['median']) for x in distances_first_values])
                res['tail_1000'] = len([x for x in distances_first_values if x >= 1000]) / count_all

                for i in range(11):
                    res['tail_%02.d' % i] = len([x for x in distances_first_values if x >= md * i / 10]) / count_all

            results.append(res)

            # TODO other tails

            # print("RESULT:\t\t\t\t\t", self.session_id, tf1, tf2, res)
        return results


def compute_min_distance(session_id, target_directory1='ciao/', target_directory2='ciao/',
                         max_distances=(5500, 2200, 1100)):  # +a list of parameters
    """Computes the min_distance couple distance distributions given
    two TFBS datasets and returns a null table Model row for
    insertion.

    Keyword arguments:
        -- ds1, ds2: GMQLDatasets containing binding sites for each TF
        and maps to TSS
        -- use_tsses: defines whether the algorithm should search for
        colocation in promoters. Use False for null distributions.
        (default: True)"""

    max_distances = sorted(max_distances, reverse=True)

    print(AnalysisResults.objects.count())

    is_same = (target_directory1 == target_directory2)

    # TODO remove
    # result_file = "results/result_file_par.txt"
    # result_file_merged = "results/result_file_merged_par.txt"

    # lock = Lock()

    list_of_tf1 = []

    for (dir_path, dir_names, file_names) in walk(target_directory1):
        list_of_tf1.extend(file_names)
        break

    print("List of tfs1:", list_of_tf1)

    if is_same:
        list_of_tf2 = list_of_tf1
    else:
        list_of_tf2 = []
        for (dir_path, dir_names, file_names) in walk(target_directory2):
            list_of_tf2.extend(file_names)
            break

    print("List of tfs2:", list_of_tf2)

    # Establish communication queues
    tasks = multiprocessing.JoinableQueue()
    results = multiprocessing.Queue()

    # Start consumers
    num_consumers = min(MAX_CPU, int(multiprocessing.cpu_count()))
    print('Creating %d consumers' % num_consumers)
    consumers = [Consumer(tasks, results, session_id, max_distances, target_directory1, target_directory2) for i in range(num_consumers)]
    # consumers = [Consumer(tasks, results)]

    for w in consumers:
        w.start()

    # Enqueue jobs
    traverse = [(tf1, tf2) for tf1 in list_of_tf1 for tf2 in list_of_tf2 if tf1 != tf2]
    if is_same:
        traverse = filter(lambda x: x[0] < x[1], traverse)
    for (tf1, tf2) in traverse:
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
            ress = results.get(timeout=1)
            for res in ress:
                save_to_db(session_id, res, is_same)
            count += 1
            print('\t\t\tA Count: ', count, ' - Result:', ress)
        except Empty:
            # print ('##timeout##')
            pass
    # Wait for all of the tasks to finish
    tasks.join()

    # Start printing results
    while not results.empty():
        ress = results.get()
        for res in ress:
            save_to_db(session_id, res, is_same)
        count += 1
        print('\t\t\tB Count: ', count, ' - Result:', ress)


def save_to_db(session_id, value_dict, is_same):
    new_result = AnalysisResults()
    new_result.session_id = session_id
    new_result.tf1 = value_dict['tf1']
    new_result.tf2 = value_dict['tf2']
    new_result.max_distance = value_dict['max_distance']

    new_result.cumulative_count_all = value_dict.get('count_all')
    new_result.cumulative_count_tss = value_dict.get('count_tss')

    new_result.average = value_dict.get('average')
    new_result.median = value_dict.get('median')
    new_result.mad = value_dict.get('mad')

    new_result.tail_00 = value_dict.get('tail_00')
    new_result.tail_01 = value_dict.get('tail_01')
    new_result.tail_02 = value_dict.get('tail_02')
    new_result.tail_03 = value_dict.get('tail_03')
    new_result.tail_04 = value_dict.get('tail_04')
    new_result.tail_05 = value_dict.get('tail_05')
    new_result.tail_06 = value_dict.get('tail_06')
    new_result.tail_07 = value_dict.get('tail_07')
    new_result.tail_08 = value_dict.get('tail_08')
    new_result.tail_09 = value_dict.get('tail_09')
    new_result.tail_10 = value_dict.get('tail_10')

    new_result.tail_1000 = value_dict.get('tail_1000')
    new_result.save()

    if is_same:
        new_result = AnalysisResults()
        new_result.session_id = session_id
        new_result.tf1 = value_dict['tf2']
        new_result.tf2 = value_dict['tf1']
        new_result.max_distance = value_dict['max_distance']

        new_result.cumulative_count_all = value_dict.get('count_all')
        new_result.cumulative_count_tss = value_dict.get('count_tss')

        new_result.average = value_dict.get('average')
        new_result.median = value_dict.get('median')
        new_result.mad = value_dict.get('mad')

        new_result.tail_00 = value_dict.get('tail_00')
        new_result.tail_01 = value_dict.get('tail_01')
        new_result.tail_02 = value_dict.get('tail_02')
        new_result.tail_03 = value_dict.get('tail_03')
        new_result.tail_04 = value_dict.get('tail_04')
        new_result.tail_05 = value_dict.get('tail_05')
        new_result.tail_06 = value_dict.get('tail_06')
        new_result.tail_07 = value_dict.get('tail_07')
        new_result.tail_08 = value_dict.get('tail_08')
        new_result.tail_09 = value_dict.get('tail_09')
        new_result.tail_10 = value_dict.get('tail_10')

        new_result.tail_1000 = value_dict.get('tail_1000')
        new_result.save()
