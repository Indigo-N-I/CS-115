# file contains events that can happen
from objects import Train, Queue, Station, Crew
import random
from queue import PriorityQueue


# general crew creation function
def gen_crew(time_left_l_bound, time_left_u_bound, cur_time):

    # gets percentage between the two times
    # multiplies by difference of times
    # adds precent to the lower to get a random number
    # between the lower and upper bounds
    time_left = random.random() * (time_left_u_bound - time_left_l_bound) + time_left_l_bound

    check_out_time = cur_time + time_left
    new_crew = Crew(check_out_time)
    return new_crew


# operational functions
global events_queue = PriorityQueue
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
    events_queue.put((cur_time, enter_queue, train))
    events_queue.put(())

    # add next train
    """
    events_queue.put((cur_time + time, arrival, train))
    """

def enter_queue(train):
    q.add_train(train, cur_time)

def exit_queue(train):
    q.remove_train(train)

    # exiting queue goes straight into station
    events_queue.put((cur_time, enter_station, train))

def enter_station(train):
    station.train_enter(train, cur_time)

    # time to unload
    Δt = 2 # dummy variable for now

    finish_time = cur_time + Δt

    events_queue.put(finish_time, exit_station, train)

def exit_station(train):
    station.train_served(train, cur_time)

    #get next train in queue
    next_train = q.next_train()
    events_queue.put((cur_time, exit_queue, next_train))
