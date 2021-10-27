import random
import simpy
RAND_NUM = random.Random()
RAND_NUM.seed(1)

class Train(object):
    ID = 0
    def __init__(self, env, dock, start_time):
        self.env = env
        self.action = env.process(self.run())
        self.crew_time_left = 12 # no random to start
        self.dock = dock
        self.unload_time = 4 # no random to start
        self.start_time = start_time
        self.id = Train.ID
        Train.ID += 1

    def run(self):
        yield self.env.timeout(self.start_time)
        print(f"train {self.id} in system at time {self.env.now}")
        hog_out_time = RAND_NUM.random() * 5 + 6
        hog_out = self.env.timeout(hog_out_time)
        print(f"train {self.id} hogs out at time {hog_out_time}")
        with self.dock.request() as req:
            # print("waiting for dock")
            # print(f"req before satisfy {req}")
            # print(req.triggered)
            while not req.triggered:
                yield req | hog_out
                if not req.triggered:
                    print(f"train {self.id} hogged out at time {self.env.now}")
                    arrival_time = RAND_NUM.random() * 1 + 2.5
                    hog_out = self.env.timeout(12)
                    yield self.env.timeout(arrival_time)
                    print(f"train {self.id} unhogs at {self.env.now}")


            print(f"train {self.id} got to dock at {self.env.now}" )
            # print(f"req after satisfy {req}")
            unload_time = RAND_NUM.random()* 1 + 4.5
            unload = self.env.process(self.unload(unload_time, 0))
            while not unload.triggered:
                unload_start = self.env.now
                yield unload | hog_out
                if not unload.triggered:
                    print(f"train {self.id} hogged out at time {self.env.now}")
                    time_passed = -(unload_start - self.env.now)
                    arrival_time = RAND_NUM.random() * 1 + 2.5
                    hog_out = self.env.timeout(12)
                    yield self.env.timeout(arrival_time)
                    print(f"train {self.id} unhogs at {self.env.now}")
                    unload = self.env.process(self.unload(unload_time, time_passed))

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

    def request(self, *args, **kwargs):
        self.data.append((self._env.now, len(self.queue)))
        # print("requested")
        return super().request(*args, **kwargs)

    def release(self, *args, **kwargs):
        self.data.append((self._env.now, len(self.queue)))
        # print("released")
        return super().release(*args, **kwargs)
