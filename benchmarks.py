import cProfile
import math
import random
import timeit
import matplotlib.pyplot as plt
from db_adapters import MongoDB
from auth_db_server import AuthDBServer

server = AuthDBServer(MongoDB())

def insert_many(n):
    for i in range(0, n):
        server.insert(random.randint(0, n))

def insert_sorted(start, end):
    for i in range(start, end):
        server.insert(i)

server.destroy_db()
cProfile.run('insert_sorted(0, 100)')
'''
def plot_avg_insertion_time(n):
    server.destroy_db()
    exec_times = []
    x_values = []
    server.destroy_db()

    for i in range(1, n):
        start_val = 2 ** (i-1)
        end_val = 2 ** i

        start = timeit.default_timer()
        insert_sorted(start_val, end_val)
        end = timeit.default_timer()

        x_values.append(end_val)
        avg_insertion_time = (end - start) / (end_val - start_val)
        exec_times.append(avg_insertion_time)
    plt.title("Avg. insertion time")
    plt.xlabel("n")
    plt.ylabel("t")
    plt.plot(x_values, exec_times)
    plt.show()

plot_avg_insertion_time(7)
plot_avg_insertion_time(7)
'''