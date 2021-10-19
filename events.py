# file contains events that can happen
from objects import Train, Queue, Station, Crew
from filre_reader import FileReader
import random
from queue import PriorityQueue
from scipy.stats import expon
import sys
import numpy as np
from collections import defaultdict

# constants
MAX_ARRIVAL_TIME = 10 ** 1
INTER_ARRIVAL = 10
interarrival_times = []

# File reading code
FILE = False
def get_next_crew():
    assert type(FILE) == FileReader, "FILE NOT CREATED PROPERLY"
    return FILE.get_next_crew()
def get_next_train():
    assert type(FILE) == FileReader, "FILE NOT CREATED PROPERLY"
    return FILE.get_next_train()
def get_next_unload():
    assert type(FILE) == FileReader, "FILE NOT CREATED PROPERLY"
    return FILE.get_next_unload()
def get_next_crew_arrive():
    assert type(FILE) == FileReader, "FILE NOT CREATED PROPERLY"
    return FILE.get_next_crew_arrive()

# operational functions
# events that are possible:
# train arrives to simulation
# train enters station
# train finishes unloading
# train exits station
# crew hogs out
# train gets new crew
def arrival(train, file = FILE):
    # print(f"Train {train} Arrived")
    global events_queue
    global cur_time
    global q
    global station
    global train_time_gen
    global crew_arrive_gen

    train.set_intime(cur_time)
    events_queue.put((cur_time, 'enter_queue', train))
    events_queue.put((train.crew.check_out_time, 'train_hogs', train))
    assert train.crew.check_out_time - cur_time > 6, 'CREW DOES NOT STAY FOR LONG ENOUGH'
    print(f"|{train} HOGOUT IN {train.crew.check_out_time - cur_time}h", end = ' ')

    if not file:
        # add next train
        train_crew_time_left = crew_arrive_gen.random() * 5 + 6
        next_train_time = train_time_gen.random()

        # exponential distribution
        expo = expon(scale = INTER_ARRIVAL)
        inv_cdf = expo.ppf

        next_train_time = inv_cdf(next_train_time)
        crew_leave_time = train_crew_time_left + cur_time + next_train_time
        new_crew = Crew(crew_leave_time)
        new_train = Train(new_crew)
        # print(f"train created: {new_train} arrives at {cur_time + next_train_time}, {new_crew}")
        assert crew_leave_time > next_train_time, 'CREW LEAVES BEFORE TRAIN COMES'
        # train does not arrive if past 1 mil
        if cur_time + next_train_time <= MAX_ARRIVAL_TIME:
            interarrival_times.append(next_train_time)
            # print("current average times:", np.average(interarrival_times))
            events_queue.put((cur_time + next_train_time, 'arrival', new_train))

    else:
        train_crew_time_left = get_next_crew()
        next_train_time = get_next_train()

        if next_train_time:
            crew_leave_time = train_crew_time_left + next_train_time
            new_crew = Crew(crew_leave_time)
            new_train = Train(new_crew)
            events_queue.put((cur_time + next_train_time, 'arrival', new_train))


    # print("new train added")
    """
    events_queue.put((cur_time + time, arrival, train))
    """

def enter_queue(train):
    # print(f"train {train} entered queue")
    global events_queue
    global cur_time
    global q
    global station
    q.add_train(train, cur_time)

    # print(q, q.queue)

def exit_queue(train):
    # print(f"train {train} exited queue")
    global events_queue
    global cur_time
    global q
    global station
    # print(q, q.queue)
    q.remove_train(train, cur_time)
    # print(q, q.queue)
    # exiting queue goes straight into station
    events_queue.put((cur_time, 'enter_station', train))
    station.train_enter(train, cur_time)

def enter_station(train, file = FILE):
    # print(f"train {train} entered station")
    global events_queue
    global cur_time
    global q
    global station
    global unload_time_gen

    # time to unload
    if not file:
        Δt = unload_time_gen.random() + 3.5
    else:
        Δt = get_next_unload()


    finish_time = cur_time + Δt

    events_queue.put((finish_time, 'finish_unload', train))

def finish_unload(train):
    print(f'|UNLOAD {train} at time {cur_time}', end=' ')
    train.unload(cur_time)
    events_queue.put((cur_time, 'exit_station', train))

def exit_station(train):
    # print(f"train {train} exited station")
    global events_queue
    global cur_time
    global q
    global station
    station.train_served(train, cur_time)


    #get next train in queue
    # print(q, q.queue)
    next_train = q.next_train()
    # print(next_train)
    if next_train:
        events_queue.put((cur_time, 'exit_queue', next_train))
    events_queue.put((cur_time, 'leave', train))

# gathers all of the train data
# then deletes the train
def leave(train):
    global times_hogged
    global cur_time
    global in_sys_time
    # print(f"train {train} left")
    train.set_outtime(cur_time)
    in_sys_time.append(train.get_insys_time())
    times_hogged[train.hog_out_count] += 1
    del train

def train_hogs(train, file = FILE):
    # print(f"train {train} hogged")
    global events_queue
    global cur_time
    global q
    global station
    global crew_arrive_gen

    if not train.is_unloaded():
        # gen next crew
        if not file:
            new_crew_arrival = crew_arrive_gen.random() * 1 + 2.5
        else:
            new_crew_arrival = get_next_crew_arrive()
        new_crew = Crew(cur_time + 12)

        train.hog_out(cur_time)
        station.train_hogged(train, cur_time)

        events = []
        # add time to events where hogged train does nothing

        # there would be easier way to do this if I implemented my own PriorityQ
        # but I got lazy just in case editing the queue screws somethign up
        # I will just dump out the queue and re-add all the events

        while not events_queue.empty():
            next_item = events_queue.get()
            # if train is hogged, the actions taken must take
            # additional time equal to how long it takes crew to get to train
            # if a train is hogged, it won't effect other trains getting hogged/unhogged
            if (next_item[2] > train or next_item[2] == train) and (next_item[1] != 'train_hogs'\
                and next_item[1] != 'train_unhog' and next_item[1] != 'arrival'):
                changed_item = (next_item[0] + new_crew_arrival, next_item[1], next_item[2])
                events.append(changed_item)
            else:
                events.append(next_item)

        for event in events:
            events_queue.put(event)
        # make sure that the only event that has 3 arguments is unhogging
        events_queue.put((new_crew_arrival + cur_time, 'train_unhog', train, new_crew))

    else:
        print("|MEANINGLESS HOG", end = ' ')

def train_unhog(train, crew):
    # print(f"train {train} unhogged")
    global events_queue
    global cur_time
    global q
    global station

    train.new_crew(crew, cur_time)
    station.crew_arrives(train, cur_time)

def main():
    global events_queue
    global cur_time
    global q
    global station
    global train_time_gen
    global crew_arrive_gen
    global unload_time_gen
    global times_hogged
    global in_sys_time

    in_sys_time = []
    times_hogged = defaultdict(int)
    events_queue = PriorityQueue()
    cur_time = 0
    q = Queue()
    station = Station()
    train_time_gen = random.Random()
    crew_arrive_gen = random.Random()
    unload_time_gen = random.Random()

    train_time_gen.seed(1)
    crew_arrive_gen.seed(2021)
    unload_time_gen.seed(2020)

    # create first train
    # add arrival of train to event queue
        # creates a new train in the queue
    # add exit queue for first train to event_queue

    train_crew_time_left = crew_arrive_gen.random() * 5 + 6
    crew_leave_time = train_crew_time_left + cur_time
    new_crew = Crew(crew_leave_time)
    new_train = Train(new_crew)

    events_queue.put((cur_time, 'arrival', new_train))
    # events_queue.put((cur_time + .000000000000000001, exit_queue, new_train))

    # loop while event queue has events:
        # set current time to time of events
        # process each event
        # if the station not serving anyone, add exit_queue to tasks

    #connections changes the string to functions
    connections = {
        'exit_queue': exit_queue,
        'train_unhog': train_unhog,
        'leave': leave,
        'exit_station': exit_station,
        'enter_station': enter_station,
        'arrival': arrival,
        'enter_queue': enter_queue,
        'train_hogs': train_hogs,
        'finish_unload': finish_unload
    }
    prev_time = 0
    cur_time = 0
    while not events_queue.empty():
        assert prev_time <= cur_time, "TIME WENT BACKWARDS"
        action = events_queue.get()
        if len(action) == 3: # everythign except train unhog
            # print(action)
            cur_time, event, train = action
            print(f"Time {cur_time}: {event} {train}", end = ' ')
            connections[event](train)
            if not station.current_serve and event == 'enter_queue':
                events_queue.put((cur_time, 'exit_queue', train))

        elif len(action) == 4: # train unhog
            cur_time, event, train, crew = action
            print(f"Time {cur_time}: {event} {train} {crew}", end = ' ')
            connections[event](train, crew)
        prev_time = cur_time
        print()

    #gather data from station
    print(f'Station data: \n\tidle time: \
        {station.idle_time / station.get_up_time()}\n\tbusy time: \
        {station.busy_time/ station.get_up_time()}\n\thogged time: \
        {station.hogged_out_time/ station.get_up_time()}\n\ttrains served: \
        {station.num_trains_served}')

    # data from trains
    print(f'Train Data: \n\tAverage In System Time: \
        {np.average(in_sys_time)}\n\tMax In System time: \
        {np.max(in_sys_time)} \n\tHistogram:')

    for key in sorted([i for i in times_hogged.keys()]):
        print("\t", key,":", times_hogged[key])

    # data from queue
    print(f'Queue Data: \n\tMax Queue Length: \
        {q.get_max_len()}\n\tAverage Queue Length: \
        {q.get_avg_len()}')


if __name__ == '__main__':
    print(sys.argv)
    if sys.argv[1] != '-s':
        MAX_ARRIVAL_TIME = float(sys.argv[2])
        INTER_ARRIVAL = float(sys.argv[1])
    else:
        train_times = sys.argv[2]
        crew_times = sys.argv[3]
        FILE = FileReader(train_times, crew_times)

    main()