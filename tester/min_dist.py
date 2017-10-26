import multiprocessing
import statistics
from collections import defaultdict
from multiprocessing import Lock, Process
from os import walk
from queue import Empty

# definitions

directory = 'cutted_joined/'

max_distance = 1100

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


lock = Lock()

list_of_tf = []

for (dir_path, dir_names, file_names) in walk(directory):
    list_of_tf.extend(file_names)
    break

list_of_tf = [
    "ARID3A",
    "MYC",
    "ATF1",
    # "ATF3",
    # "ATF4",
    # "BHLHE40"
]
print("List of tfs:", list_of_tf)


def read(tf):
    temp_tf = defaultdict(list)
    for line in open(directory + tf):
        s = line.strip().split("\t")
        # TODO change location
        tss_val = s[3] if len(s) >= 2 else None
        tss_val = tss_val if tss_val != '-1' else None
        tss = set([int(t) for t in tss_val.split(",")]) if tss_val else None
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
            out_file_merged.write("\t".join([tf1, tf2, str(dist), str(count_all_temp), str(count_tss_temp), str(cumulative_count_all), str(cumulative_count_tss)]) + "\n")
        out_file_merged.flush()
        # out_file.close()

    count_all = len(distances)
    mean = statistics.mean(distances)
    median = statistics.median(distances)
    mad = statistics.median([abs(x - median) for x in distances])
    tail1000 = len([x for x in distances if x >= 1000]) / count_all

    tails = []
    for i in range(11): # TODO range(1,10)
        tails.append(len([x for x in distances if x >= max_distance*i/10]) / count_all)


    #TODO other tails

    print("RESULT:", tf1, tf2, max_distance, count_all, count_tss, mean, median, mad, tail1000, tails)


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
    for (tf1, tf2) in [(tf1, tf2) for tf1 in list_of_tf for tf2 in list_of_tf if tf1 < tf2]:
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
