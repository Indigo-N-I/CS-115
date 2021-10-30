import simpy
from objects import Train, Dock
from functools import partial, wraps

env = simpy.Environment()
dock = Dock(env, capacity=1)

def monitor(data, resource):
    item = (
    resource._env.now,  # The current simulation time
    resource.count,  # The number of users
    len(resource.queue),  # The number of queued processes
    )
    if item[2] > data['Max Queue']:
        data['Max Queue'] = item[2]
    print(item)
    # # either there is a user currently using or user in queue
    # if (item[1] > 0 or item[2] > 0) and not (data['Prev data'][1] > 0 or data['Prev data'][2] > 0):
    #     print(f"busy at time {item[0]}")
    #     data['Busy Time'] -= item[0]
    # # no one in queue and not in use
    if item[1] == 0 and item[2] == 0:
        data['Busy Time'] += item[0]
        print(f"no longer busy at time {item[0]}, total busy time {data['Busy Time']}")
    elif data['Prev data'][1] == data['Prev data'][2] == 0:
        print(f"busy at time {item[0]}")
        data['Busy Time'] -= item[0]

    # if the queue incrases in length
    # if item[2] > data['Prev data'][2]:
    #     data["Total Length"] -= item[0]
    # elif item[2] < data['Prev data'][2]:
    #     data['Total Length'] += item[0]

    data["Prev data"] = item
    data['total time'] = item[0]
    data['total data'].append(item)
    
def patch_resource(resource, pre=None, post=None):
     """Patch *resource* so that it calls the callable *pre* before each
     put/get/request/release operation and the callable *post* after each
     operation.  The only argument to these functions is the resource
     instance.

     """
     def get_wrapper(func):
         # Generate a wrapper for put/get/request/release
         @wraps(func)
         def wrapper(*args, **kwargs):
             # This is the actual wrapper
             # Call "pre" callback
             if pre:
                 pre(resource)

             # Perform actual operation
             ret = func(*args, **kwargs)

             # Call "post" callback
             if post:
                 post(resource)

             return ret
         return wrapper

     # Replace the original operations with our wrapper
     for name in ['put', 'get', 'request', 'release']:
         if hasattr(resource, name):
             setattr(resource, name, get_wrapper(getattr(resource, name)))



a = Train(env, dock, 0)

data = {"Max Queue":0,
        "Total Length": 0,
        "Busy Time": 0,
        "Idle Time": 0,
        "Prev data": (0,0,0),
        "total time": 0,
        "total data": [(0,0,0)]}
monitor = partial(monitor, data)
patch_resource(dock, post = monitor)

env.run(until = 100000)
print(data)
print(dock.length_data/dock.total_time, dock.total_time)
