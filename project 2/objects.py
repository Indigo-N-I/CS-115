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

    # ID serves for sanity and to check how many trains created
    ID = 0

    # data gathering variables
    MAX_TIME_IN_SYSTEM = 0
    AVG_TIME_IN_SYSTEM = 0
    HOG_OUT_COUNT = []
    HOG_OUT_TIME = 0

    def __init__(self, env, dock, start_time):
        self.env = env
        self.action = env.process(self.run())
        self.dock = dock
        self.unload_time = UNLOAD_NUM.random()* 1 + 3.5
        self.start_time = start_time
        self.id = Train.ID
        self.exit_time = start_time
        Train.ID += 1
        self.hog_outs = 0
        self.hog_out_time = 0

    def run(self):
        next_train_time = -math.log(1-NEXT_TRAIN_NUM.random()) * 10

        # all trains are to be created at the start
        # because i'm dumb and couldn't figure out how to make them systematically get created
        # but it does not run into memory issues as of yet so evrything's alright so far
        if not self.start_time + next_train_time > 1000000:
            next_train = Train(self.env, self.dock, self.start_time + next_train_time)

        # when train enters the system
        yield self.env.timeout(self.start_time)
        print(f"train {self.id} in system at time {self.env.now}")

        # once entered, there is hog out time for 6 - 11h
        hog_out_time = HOG_OUT_NUM.random() * 5 + 6
        hog_out = self.env.timeout(hog_out_time)
        print(f"train {self.id} hogs out at time {hog_out_time}")

        # Train will request to pull into the dock
        with self.dock.request() as req:

            # while the train is not in the dock yet
            while not req.triggered:
                # either hog out or get into dock
                # whichever one comes first
                yield req | hog_out

                # if hog out happens first
                if not req.triggered:
                    self.hog_outs += 1
                    print(f"train {self.id} hogged out at time {self.env.now}")

                    # generate when the next crew will show up
                    arrival_time = ARRIVAL_NUM.random() * 1 + 2.5
                    hog_out = self.env.timeout(12)

                    # tell crew to show up
                    yield self.env.timeout(arrival_time)
                    print(f"train {self.id} unhogs at {self.env.now}")

                    # if the dock is now availble when the crew shows up
                    # it means that the system was hogged out for some time
                    # so we add the hogged out time to the system
                    if self.dock.is_avalible():
                        self.hog_out_time += self.env.now - self.dock.get_avalible()


            # assert Train.Prev_in_dock == self.id-1, "Trains went out of order"
            # Train.Prev_in_dock = self.id
            print(f"train {self.id} got to dock at {self.env.now}" )

            # get an amount of time for unload
            unload_time = self.unload_time
            unload = self.env.process(self.unload(unload_time, 0))

            # while the train has not been unloaded
            while not unload.triggered:

                # unload start used to save when unload starts
                # so that if there is hogout, remaining time can be calculated
                unload_start = self.env.now

                # try to finish unloading or hog out
                yield unload | hog_out

                # if there is a hogout before unloading is finished
                if not unload.triggered:
                    self.hog_outs += 1
                    print(f"train {self.id} hogged out at time {self.env.now}")

                    #calculate how much unloading has happened
                    time_passed = -(unload_start - self.env.now)
                    arrival_time = ARRIVAL_NUM.random() * 1 + 2.5

                    self.hog_out_time += arrival_time
                    hog_out = self.env.timeout(12)
                    yield self.env.timeout(arrival_time)
                    print(f"train {self.id} unhogs at {self.env.now}")

                    # unload resumes after unhog
                    unload = self.env.process(self.unload(unload_time, time_passed))

                    # no need to add another hog out time because unloading
                    # takes less time than crews hogging out
                    # so even in worst case senario, can only hog out one time during
                    # process of unloading

            #save when the train exits sim
            self.exit_time = self.env.now

            # saving data
            if self.exit_time - self.start_time > Train.MAX_TIME_IN_SYSTEM:
                Train.MAX_TIME_IN_SYSTEM = self.exit_time - self.start_time
            Train.AVG_TIME_IN_SYSTEM += (self.exit_time - self.start_time) / Train.ID
            Train.HOG_OUT_COUNT.append(self.hog_outs)
            Train.HOG_OUT_TIME += self.hog_out_time
            return

    def unload(self, unload_time, already_spent = 0):
        print(f"unloading starting at {self.env.now} for train {self.id} for {unload_time - already_spent}h")

        # try to unload the train in time alloted
        # can get interuppted by hog out
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
        self.total_time = 0
        self.prev_time = 0
        # self.prev_train = 0
        self.avil_time = -1

    def request(self, *args, **kwargs):
        self.data.append((self._env.now, len(self.queue)))

        # time total length subtract when a request occures
        self.length_data -= self._env.now
        self.total_time = self._env.now
        return super().request(*args, **kwargs)

    def release(self, *args, **kwargs):
        self.total_time = self._env.now
        self.data.append((self._env.now, len(self.queue)))

        # save when the dock is avalible
        if len(self.users) == 0:
            self.avil_time = self._env.now

        # time total length add when a request occures
        self.length_data += self._env.now
        return super().release(*args, **kwargs)

    # used to check if dock is avalible when train unhoggs
    def get_avalible(self):
        return self.avil_time

    def is_avalible(self):
        return (len(self.users) == 0)