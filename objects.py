# objects in this simulation will be
# Train
# Crew
# Queue
# Station


# Trains will have a crew, times hogged out, whether or not is hogged out
class Train():
    cur_id = 1
    def __init__(self, crew):
        self.id = cur_id
        cur_id += 1
        self.crew = crew
        self.hogged_out = False
        self.hog_out_count = 0
        # for sanity checking
        self.unloaded = False

    def __eq__(self, other):
        return self.id == other.id

    def unload(self, time):
        self.unloaded = True

    def hog_out(self, time):
        assert not self.crew.still_working(time), f'CREW OF TRAIN {self.id} LEAVING ON CLOCK'
        self.crew = None
        self.hogged_out = True
        self.hot_out_count += 1

    def new_crew(self, crew, time):
        self.crew = crew
        self.hogged_out = False

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
        self.id = crew_id
        crew_id += 1

    def still_working(self, time):
        if time > self.check_out_time:
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

        self.busy_start = self.busy_end = self.idle_start = self.idle_end = self.hog_start = self.hog_end = 0

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

        assert self.busy_end > self.busy_start, 'STATION ENDS BEING BUSY BEFORE BEING BUSY'
        self.busy_time += self.busy_end - self.busy_start
        self.current_serve = None

    def train_enter(self, train, time):
        assert not train.is_unloaded(), f"TRAIN {train.get_id()} ENTERING STATION UNLOADED"
        assert not self.current_serve, "TRAIN STARTING SERVICE WITH DIFFERENT TRAIN IN STATION"

        if train.is_hogged():
            self.hog_start = time
            self.hogged = True

        self.idle_end = time
        self.busy_start = time

        assert self.idle_end > self.idle_start, 'STATION ENDS BEING IDLE BEFORE BEING IDLE'
        self.idle_time += self.idle_end - self.idle_start
        self.current_serve = train

    def train_hogged(self, train, time):
        # don't care if train is hogged but we are not serving the train
        if train == self.current_serve:
            assert not train.get_crew(), f'TRAIN {train.get_id()} IS HOGGED OUT WITH CREW'

            self.hog_start = time
            self.hogged = True

    def crew_arrives(self, train, time):
        assert train.get_crew(), f'TRAIN {train.get_id()} HAS NO CREW BUT CREW HAS ARRIVED'
        self.hogged = False
        self.hog_end = time
        assert self.hog_end > self.hog_start, 'HOG OUT ENDS BEFORE STARTING'

        self.hogged_out_time += self.hog_end - self.hog_start

# the queue will contain the order that trains arrived in
class Queue():
    def __init__(self):
        self.queue = []
        self.length = 0

    def add_train(self, train, time):
        self.queue.append(train)
        self.length += 1

    def remove_train(self, train, time):
        assert self.queue[0] == train, f'WRONG TRAIN ({train.get_id()} vs {self.queue[0].get_id()})AT THE FRONT OF QUEUE'

        self.queue.pop()

    def next_train(self):
        return self.queue[0]
