# objects in this simulation will be
# Train
# Crew
# Queue
# Station


# Trains will have a crew, times hogged out, whether or not is hogged out
class Train():
    cur_id = 1
    def __init__(self, crew):
        self.id = int(Train.cur_id)
        Train.cur_id += 1
        self.crew = crew
        self.hogged_out = False
        self.hog_out_count = 0
        # for sanity checking
        self.unloaded = False
        self.in_time = self.out_time = 0

    def __eq__(self, other):
        if other:
            return self.id == other.id
        return False

    def __repr__(self):
        return f"Train {self.id}"

    def __lt__(self, other):
        if other:
            return self.id < other.id
        return False

    def __gt__(self, other):
        if other:
            return self.id > other.id
        return False

    def set_intime(self, time):
        self.in_time = time

    def set_outtime(self,time):
        self.out_time = time

    def get_insys_time(self):
        return self.out_time - self.in_time

    def unload(self, time):
        # print(self.id, "unloaded at time", time)
        self.unloaded = True

    def hog_out(self, time):
        assert not self.crew.still_working(time), f'CREW OF TRAIN {self.id} LEAVING ON CLOCK'
        self.crew = None
        self.hogged_out = True
        self.hog_out_count += 1
        print(f'TRAIN {self.id} HOGGED', end = ' ')

    def new_crew(self, crew, time):
        self.crew = crew
        self.hogged_out = False
        print(f'TRAIN {self.id} UNHOGGED', end = ' ')

    def is_hogged(self):
        return self.hogged_out

    def is_unloaded(self):
        return self.unloaded

    def get_crew(self):
        return self.crew

    def get_id(self):
        return self.id

# Crew will only enable sanity checks
# contains when the crew leaves
# crew has an ID that does not do anything as of now
class Crew():
    crew_id = 0
    def __init__(self, check_out_time):
        self.check_out_time = check_out_time
        self.id = Crew.crew_id
        Crew.crew_id += 1

    def __repr__(self):
        return f"Crew {self.id} checkout time: {self.check_out_time}"

    def still_working(self, time):
        # print(time, self.check_out_time)
        if time >= self.check_out_time:
            return False
        return True

    def get_checkout_time(self):
        return self.check_out_time

# Station will keep most of the information
# and statistics at the end
# The station will not provide the train the crew
class Station():
    def __init__(self):
        self.num_trains_served = 0
        self.busy_time = 0
        self.idle_time = 0
        self.hogged_out_time = 0

        self.end_time = self.busy_start = self.busy_end = self.idle_start = self.idle_end = self.hog_start = self.hog_end = 0

        self.current_serve = None

        # sanity check
        self.hogged = False

    def train_served(self, train, time):
        assert self.current_serve, "TRAIN ENDING SERVICE WITHOUT TRAIN IN STATION"
        assert train.is_unloaded(), f"TRAIN {train.get_id()} LEAVING STATION LOADED"
        assert not train.is_hogged(), f"TRAIN {train.get_id()} LEAVING STATION HOGGED OUT"
        assert train.get_crew(), f"TRAIN {train.get_id()} IS LEAVING WITHOUT CREW"
        assert not self.hogged, 'TRAIN EXITING STATION WHILE STATION IS HOGGED'
        self.num_trains_served += 1
        self.busy_end = time
        self.idle_start = time

        assert self.busy_end >= self.busy_start, 'STATION ENDS BEING BUSY BEFORE BEING BUSY'
        self.busy_time += self.busy_end - self.busy_start
        self.current_serve = None
        self.end_time = time

    def train_enter(self, train, time):
        assert not train.is_unloaded(), f"TRAIN {train.get_id()} ENTERING STATION UNLOADED"
        assert not self.current_serve, "TRAIN STARTING SERVICE WITH DIFFERENT TRAIN IN STATION"

        if train.is_hogged():
            self.hog_start = time
            assert not self.hogged, "HOGGING WHEN ALREADY HOGGED"
            self.hogged = True
            print("|SERVER HOGGED", end = ' ')

        self.idle_end = time
        self.busy_start = time

        assert self.idle_end >= self.idle_start, f'STATION ENDS BEING IDLE BEFORE BEING IDLE {self.idle_end}, {self.idle_start}'
        # print(f"train {train} entered")
        # print(f'adding {self.idle_end - self.idle_start} to idle time')
        self.idle_time += self.idle_end - self.idle_start
        self.current_serve = train

    def train_hogged(self, train, time):
        # don't care if train is hogged but we are not serving the train
        if train == self.current_serve:
            assert not train.get_crew(), "HOGGED TRAIN CREW NOT HOGGED"
            # print("Train being served and is hogged", end = '')
            assert not train.get_crew(), f'TRAIN {train.get_id()} IS HOGGED OUT WITH CREW'

            self.hog_start = time
            self.hogged = True
            print("|SERVER HOGGED", end = ' ')

    def crew_arrives(self, train, time):
        assert train.get_crew(), f'TRAIN {train.get_id()} HAS NO CREW BUT CREW HAS ARRIVED'
        if train == self.current_serve:
            assert self.hogged, "UNHOGGING WHEN NOT HOGGED"
            # print('\n',train, self.current_serve)
            self.hogged = False
            self.hog_end = time
            assert self.hog_end > self.hog_start, 'HOG OUT ENDS BEFORE STARTING'
            print("|SERVER UNHOGGED", end = '')
            self.hogged_out_time += self.hog_end - self.hog_start

    def get_up_time(self):
        return self.end_time

# the queue will contain the order that trains arrived in
class Queue():
    def __init__(self):
        self.queue = []
        self.length = 0
        self.max_len = 0
        self.total_train_time = 0
        self.total_time = 0

    def add_train(self, train, time):
        self.queue.append(train)
        self.length += 1
        print(f'|Q = {self.length}', end=' ')
        if self.length > self.max_len:
            self.max_len = self.length
        self.total_train_time -= time

    def remove_train(self, train, time):
        assert self.queue[0] == train, f'WRONG TRAIN ({train.get_id()} vs {self.queue[0].get_id()})AT THE FRONT OF QUEUE'
        # print("inside of remove train", self.queue)
        self.queue.pop(0)
        self.length -= 1
        # print("after pop",self.queue)
        print(f'|Q = {self.length}', end = ' ')
        self.total_train_time += time
        self.total_time = time

    def next_train(self):
        if len(self.queue) > 0:
            return self.queue[0]
        return False

    def get_max_len(self):
        return self.max_len

    def get_avg_len(self):
        return self.total_train_time/self.total_time
