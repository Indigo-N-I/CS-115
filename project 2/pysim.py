import simpy
from objects import Train, Crew

env = simpy.Environment()
dock = simpy.Resource(env, capacity=1)

for i in range(10):
    a = Train(env, dock, (i+1)*2)
    # b = Crew(env, a)
env.run(until = 100)