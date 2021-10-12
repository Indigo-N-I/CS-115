# file contains events that can happen
from objects import Train, Queue, Station, Crew
import random
from queue import PriorityQueue

# operational functions
global events_queue = PriorityQueue()
global cur_time = 0
global q = Queue()
global station = Station()

# events that are possible:
# train arrives to simulation
# train enters station
# train finishes unloading
# train exits station
# crew hogs out
# train gets new crew

def arrival(train):
    global events_queue
    global cur_time
    global q
    global station
    events_queue.put((cur_time, enter_queue, train))
    events_queue.put((train.crew.check_out_time, train_hogs, train))

    # add next train
    """
    events_queue.put((cur_time + time, arrival, train))
    """

def enter_queue(train):
    global events_queue
    global cur_time
    global q
    global station
    q.add_train(train, cur_time)

def exit_queue(train):
    global events_queue
    global cur_time
    global q
    global station
    q.remove_train(train)

    # exiting queue goes straight into station
    events_queue.put((cur_time, enter_station, train))

def enter_station(train):
    global events_queue
    global cur_time
    global q
    global station
    station.train_enter(train, cur_time)

    # time to unload
    Δt = 2 # dummy variable for now

    finish_time = cur_time + Δt

    events_queue.put(finish_time, exit_station, train)

def exit_station(train):
    global events_queue
    global cur_time
    global q
    global station
    station.train_served(train, cur_time)

    #get next train in queue
    next_train = q.next_train()
    events_queue.put((cur_time, exit_queue, next_train))

def train_hogs(train):
    global events_queue
    global cur_time
    global q
    global station

    # gen next crew
    new_crew_arrival = random.random() * 1 + 2.5
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
        if next_item[2] == train:
            changed_item = (next_item[0] + new_crew_arrival, next_item[1], train)
            events.append(changed_item)
        else:
            events.append(next_item)

    for event in events:
        events_queue.put(event)

    # make sure that the only event that has 3 arguments is unhogging
    events_queue.put((new_crew_arrival + cur_time, train_unhog, train, new_crew))

def train_unhog(train, crew):
    global events_queue
    global cur_time
    global q
    global station

    train.new_crew(crew, cur_time)
    station.crew_arrives(train, cur_time)
