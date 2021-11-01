import random, math
import simpy
HOG_OUT_NUM = random.Random()
ARRIVAL_NUM = random.Random()
UNLOAD_NUM = random.Random()
CREW_NUM = random.Random()
NEXT_TRAIN_NUM = random.Random(256)

HOG_OUT_NUM.seed(1)
ARRIVAL_NUM.seed(4)
UNLOAD_NUM.seed(16)
CREW_NUM.seed(64)
NEXT_TRAIN_NUM.seed(256)


class Train(object):
    ID = 0
    MAX_TIME_IN_SYSTEM = 0
    AVG_TIME_IN_SYSTEM = 0
    HOG_OUT_COUNT = []
    HOG_OUT_TIME = 0
    # HOG_OUT_TIME = 0
    # Prev_in_dock = -1
    def __init__(self, env, dock, start_time):
        self.env = env
        self.action = env.process(self.run())
        self.crew_time_left = CREW_NUM.random()*5 + 6
        self.dock = dock
        self.unload_time = UNLOAD_NUM.random()* 1 + 3.5
        self.start_time = start_time
        self.id = Train.ID
        self.exit_time = start_time
        Train.ID += 1
        self.hog_outs = 0
        self.hog_out_time = 0
        # print(f"train {self.id} created")
        # print(f"Current time at creation is {env.now}")

    def run(self):
        next_train_time = -math.log(1-NEXT_TRAIN_NUM.random()) * 10
        # yield self.env.process(next_train.run())
        if not self.start_time + next_train_time > 1000000:
            next_train = Train(self.env, self.dock, self.start_time + next_train_time)
        yield self.env.timeout(self.start_time)
        print(f"train {self.id} in system at time {self.env.now}")
        hog_out_time = HOG_OUT_NUM.random() * 5 + 6
        hog_out = self.env.timeout(hog_out_time)
        print(f"train {self.id} hogs out at time {hog_out_time}")
        # hog_outs = 0
        with self.dock.request() as req:
            # print("waiting for dock")
            # print(f"req before satisfy {req}")
            # print(req.triggered)
            while not req.triggered:
                yield req | hog_out
                if not req.triggered:
                    self.hog_outs += 1
                    print(f"train {self.id} hogged out at time {self.env.now}")
                    arrival_time = ARRIVAL_NUM.random() * 1 + 2.5
                    hog_out = self.env.timeout(12)
                    yield self.env.timeout(arrival_time)
                    print(f"train {self.id} unhogs at {self.env.now}")
                    if self.dock.is_avalible():
                        self.hog_out_time += self.env.now - self.dock.get_avalible()
            # assert Train.Prev_in_dock == self.id-1, "Trains went out of order"
            # Train.Prev_in_dock = self.id
            print(f"train {self.id} got to dock at {self.env.now}" )
            # print(f"req after satisfy {req}")
            unload_time = self.unload_time
            unload = self.env.process(self.unload(unload_time, 0))
            while not unload.triggered:
                unload_start = self.env.now
                yield unload | hog_out
                if not unload.triggered:
                    self.hog_outs += 1
                    print(f"train {self.id} hogged out at time {self.env.now}")
                    time_passed = -(unload_start - self.env.now)
                    arrival_time = ARRIVAL_NUM.random() * 1 + 2.5
                    self.hog_out_time += arrival_time
                    hog_out = self.env.timeout(12)
                    yield self.env.timeout(arrival_time)
                    print(f"train {self.id} unhogs at {self.env.now}")
                    unload = self.env.process(self.unload(unload_time, time_passed))
            self.exit_time = self.env.now
            if self.exit_time - self.start_time > Train.MAX_TIME_IN_SYSTEM:
                Train.MAX_TIME_IN_SYSTEM = self.exit_time - self.start_time
            Train.AVG_TIME_IN_SYSTEM += (self.exit_time - self.start_time) / Train.ID
            Train.HOG_OUT_COUNT.append(self.hog_outs)
            Train.HOG_OUT_TIME += self.hog_out_time
            return

    def unload(self, unload_time, already_spent = 0):
        print(f"unloading starting at {self.env.now} for train {self.id} for {unload_time - already_spent}h")
        try:
            yield self.env.timeout(unload_time - already_spent)
            print(f"unload successful for train {self.id} at time {self.env.now}")
        except simpy.Interrupt as i:
            print(f"unload interupted at {self.env.now} due to hogout")
        except Exception as e:
            print("other exception happened", e)

class Dock(simpy.Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = []
        self.length_data = 0
        self.busy_start= self.busy_end= self.idle_start= self.idle_end= self.idle_time= self.busy_time = 0
        self.req = 0
        self.released = 0
        self.total_time = 0
        self.prev_time = 0
        # self.prev_train = 0
        self.avil_time = -1

    def request(self, *args, **kwargs):
        self.data.append((self._env.now, len(self.queue)))
        print("requested")
        self.length_data -= self._env.now
        self.req += 1
        # print(self.queue)
        # assert self.prev_time < self._env.now, " Time went backwards"
        self.total_time = self._env.now
        return super().request(*args, **kwargs)

    def release(self, *args, **kwargs):
        self.total_time = self._env.now
        self.data.append((self._env.now, len(self.queue)))
        print("released")
        # print(len(self.queue))
        if len(self.users) == 0:
            self.avil_time = self._env.now
        # print(self.queue)
        # assert self.prev_time < self._env.now, " Time went backwards"
        self.length_data += self._env.now
        self.released += 1
        return super().release(*args, **kwargs)

    def get_avalible(self):
        return self.avil_time

    def is_avalible(self):
        return (len(self.users) == 0)