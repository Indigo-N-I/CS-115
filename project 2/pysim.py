import simpy
from objects import Train, Dock, reset_random
from filre_reader import FileReader
from functools import partial, wraps
from collections import defaultdict
import sys
import numpy as np
import scipy.stats



FILE = False
MAX_ARRIVAL_TIME = 1000000
INTER_ARRIVAL = 10
# monitor is edited from simpy's examples
def monitor(data, resource):
    item = (
        resource._env.now,  # The current simulation time
        resource.count,  # The number of users
        len(resource.queue),  # The number of queued processes
    )
    if item[2] > data['Max Queue']:
        data['Max Queue'] = item[2]
    # print(item)
    # # either there is a user currently using or user in queue
    # # no one in queue and not in use

    # there is no one in the queue and no one waiting in the queue
    if item[1] == 0 and item[2] == 0:
        data['Busy Time'] += item[0]
        print(f"no longer busy at time {item[0]}, total busy time {data['Busy Time']}")
    # in the previous state, there was no one waiting for or at the dock
    elif data['Prev data'][1] == data['Prev data'][2] == 0:
        print(f"busy at time {item[0]}")
        data['Busy Time'] -= item[0]

    data["Prev data"] = item
    data['total time'] = item[0]

# patch resource also copied from simpy's example
def patch_resource(resource, pre=None, post=None):
    """Patch *resource* so that it calls the callable *pre* before each
    put/get/request/release operation and the callable *post* after each
    operation.  The only argument to these functions is the resource
    instance.

    """

    def get_wrapper(func):
        # Generate a wrapper for put/get/request/release
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This is the actual wrapper
            # Call "pre" callback
            if pre:
                pre(resource)

            # Perform actual operation
            ret = func(*args, **kwargs)

            # Call "post" callback
            if post:
                post(resource)

            return ret

        return wrapper

    # Replace the original operations with our wrapper
    for name in ['put', 'get', 'request', 'release']:
        if hasattr(resource, name):
            setattr(resource, name, get_wrapper(getattr(resource, name)))

# confidence interval calculation from stock overflow
def calc_CI(data, confidence=0.99):
    a = 1.0 * np.array(data)
    n = len(a)
    m, se = np.mean(a), scipy.stats.sem(a)
    h = se * scipy.stats.t.ppf((1 + confidence) / 2., n-1)
    return m, m-h, m+h

def main(test_inter = False):
    if not test_inter:
        if sys.argv[1] != '-s':
            MAX_ARRIVAL_TIME = float(sys.argv[2])
            INTER_ARRIVAL = float(sys.argv[1])
            try:
                LOOPS = int(sys.argv[3])
            except IndexError as e:
                print("Only one loop requested")
                LOOPS = 1
            FILE = False
            start_time = 0
        else:
            train_times = sys.argv[2]
            crew_times = sys.argv[3]
            FILE = FileReader(train_times, crew_times)
            start_time = FILE.get_next_train()
    else:
        MAX_ARRIVAL_TIME = 1e6
        INTER_ARRIVAL = test_inter
        try:
            LOOPS = int(sys.argv[3])
        except IndexError as e:
            print("Only one loop requested")
            LOOPS = 1
        FILE = False
        start_time = 0

    data_list = defaultdict(list)

    for l in range(LOOPS):
        Train.reset()
        reset_random(l + 1)
        env = simpy.Environment()
        dock = Dock(env, capacity=1)
        a = Train(env, dock, start_time)
        Train.set_info(FILE, MAX_ARRIVAL_TIME, INTER_ARRIVAL)

        data = {"Max Queue": 0,
                "Total Length": 0,
                "Busy Time": 0,
                "Idle Time": 0,
                "Prev data": (0, 0, 0),
                "total time": 0,
                "total data": [(0, 0, 0)]}
        monitor_1 = partial(monitor, data)
        patch_resource(dock, post=monitor_1)

        # *2 so that all trains are able to leave
        env.run(until=MAX_ARRIVAL_TIME*2)
        busy_percent = data['Busy Time']/data["total time"]
        idle_percent = 1 - busy_percent
        max_length = data['Max Queue']
        avg_length = dock.length_data / dock.total_time
        avg_wait_time = Train.AVG_TIME_IN_SYSTEM
        max_time_in_system = Train.MAX_TIME_IN_SYSTEM
        histogram = Train.HOG_OUT_COUNT
        hog_out_time = Train.HOG_OUT_TIME/dock.total_time
        # print(data)
        # print(data['Busy Time']/data["total time"])
        # print(dock.length_data / dock.total_time, dock.total_time)
        # print(Train.AVG_TIME_IN_SYSTEM, Train.MAX_TIME_IN_SYSTEM, Train.HOG_OUT_COUNT.count(0), Train.HOG_OUT_COUNT.count(1), Train.HOG_OUT_COUNT.count(2))
        # print(Train.HOG_OUT_TIME/dock.total_time)
        data_list['Busy Percent'].append(busy_percent)
        data_list['Idle Percent'].append(idle_percent)
        data_list["Max Length"].append(max_length)
        data_list["Avg Length"].append(avg_length)
        data_list['Avg Wait Time'].append(avg_wait_time)
        data_list['Max Time In System'].append(max_time_in_system)
        data_list['Histogram'].append(histogram)
        data_list["Hog Out Percent"].append(hog_out_time)
    if test_inter:
        return data_list['Avg Wait Time'][0]

def test_inter():
    prev = defaultdict(int)
    for i in range(50):
        inter_time = 10 - i / 5
        prev[inter_time] = main(inter_time)
    print(prev)

if __name__ == "__main__":
    main()