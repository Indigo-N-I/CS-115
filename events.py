# file contains events that can happen
from objects import Train, Queue, Station, Crew
import random
from queue import PriorityQueue
from scipy.stats import expon

# operational functions


# events that are possible:
# train arrives to simulation
# train enters station
# train finishes unloading
# train exits station
# crew hogs out
# train gets new crew

def arrival(train):
    print(f"Train {train} Arrived")
    global events_queue
    global cur_time
    global q
    global station
    global train_time_gen
    global crew_arrive_gen

    events_queue.put((cur_time, 'enter_queue', train))
    events_queue.put((train.crew.check_out_time, 'train_hogs', train))

    # add next train
    train_crew_time_left = crew_arrive_gen.random() * 5 + 6
    next_train_time = train_time_gen.random()

    # exponential distribution
    expo = expon(scale = 10)
    inv_cdf = expo.ppf

    next_train_time = inv_cdf(next_train_time)
    crew_leave_time = train_crew_time_left + cur_time + next_train_time
    new_crew = Crew(crew_leave_time)
    new_train = Train(new_crew)

    events_queue.put((cur_time + next_train_time, 'arrival', new_train))

    # print("new train added")
    """
    events_queue.put((cur_time + time, arrival, train))
    """

def enter_queue(train):
    print(f"train {train} entered queue")
    global events_queue
    global cur_time
    global q
    global station
    q.add_train(train, cur_time)

    # print(q, q.queue)

def exit_queue(train):
    print(f"train {train} exited queue")
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

def enter_station(train):
    print(f"train {train} entered station")
    global events_queue
    global cur_time
    global q
    global station
    global unload_time_gen

    # time to unload
    Δt = unload_time_gen.random() + 3.5
    train.unload(cur_time)

    finish_time = cur_time + Δt

    events_queue.put((finish_time, 'exit_station', train))

def exit_station(train):
    print(f"train {train} exited station")
    global events_queue
    global cur_time
    global q
    global station
    station.train_served(train, cur_time)

    #get next train in queue
    print(q, q.queue)
    next_train = q.next_train()
    print(next_train)
    if next_train:
        events_queue.put((cur_time, 'exit_queue', next_train))
    events_queue.put((cur_time+.0000000001, 'leave', train))

def leave(train):
    print(f"train {train} left")
    del train

def train_hogs(train):
    print(f"train {train} hogged")
    global events_queue
    global cur_time
    global q
    global station
    global crew_arrive_gen


    if not train.is_unloaded():
        # gen next crew
        new_crew_arrival = crew_arrive_gen.random() * 1 + 2.5
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
                and next_item[1] != 'train_unhog'):
                changed_item = (next_item[0] + new_crew_arrival, next_item[1], next_item[2])
                events.append(changed_item)
            else:
                events.append(next_item)

        for event in events:
            events_queue.put(event)

        # make sure that the only event that has 3 arguments is unhogging
        events_queue.put((new_crew_arrival + cur_time, 'train_unhog', train, new_crew))

def train_unhog(train, crew):
    print(f"train {train} unhogged")
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
        'train_hogs': train_hogs
    }

    while not events_queue.empty():
        action = events_queue.get()
        if len(action) == 3: # everythign except train unhog
            print(action)
            cur_time, event, train = action
            connections[event](train)
            if not station.current_serve and event == enter_queue:
                events_queue.put((cur_time + .000000000000000001, 'exit_queue', train))
        elif len(action) == 4: # train unhog
            cur_time, event, train, crew = action
            connections[event](train, crew)
        if cur_time > 10**8:
            break
        print(f"simulated to time {cur_time}, {events_queue.queue} \n")
    print(events_queue)

if __name__ == '__main__':
    print('here')
    main()