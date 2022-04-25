import cProfile
import math
import numpy as np
import random
import timeit
import matplotlib.pyplot as plt

from cache import Cache
from db_adapters import MongoDB
from auth_db_server import AuthDBServer

dbi = MongoDB()
cache=Cache(dbi, write_to_db=False)
server = AuthDBServer(dbi, cache)

def insert_many(start, end):
    for i in range(start, end):
        server.insert(random.randint(0, 2 ** 128))

def insert_sorted(start, end):
    for i in range(start, end):
        server.insert(i)

def moving_average(x, w):
    return np.convolve(x, np.ones(w), 'valid') / w

server.destroy_db()
#cProfile.run('insert_sorted(0, 1000)')

def plot_avg(n, interval_length, function):
    server.destroy_db()
    y_values = []
    x_values = []

    for j in range(1, n, interval_length):

        start = timeit.default_timer()
        for i in range(j, j + interval_length):
            if i == 13641:
                print("hej")
            else:
                function(i)
        end = timeit.default_timer()

        avg_y = (end - start) / interval_length
        y_values.append(avg_y)
        x_values.append(j)

    for v in y_values:
        if v > 5.0720000000015195 * 10 ** (-5) * 20:
            print("hallelujah")
            index = y_values.index(v)
            print(v)
            print("x: ", x_values[index])
    plt.title("Avg. insertion time")
    plt.xlabel("n")
    plt.ylabel("t")
    print(len(y_values))
    print(y_values)
    ma_w = 1
    y_values = moving_average(y_values, ma_w).tolist()
    print("After MA")
    print(len(y_values))
    print(y_values)
    x_values = x_values[ma_w - 1:]
    plt.plot(x_values, y_values)
    plt.show()

def plot_avg_insertion_time(n):
    server.destroy_db()
    exec_times = []
    x_values = []

    for i in range(1, n):
        start_val = 2 ** (i-1)
        end_val = 2 ** i

        start = timeit.default_timer()
        insert_many(start_val, end_val)
        end = timeit.default_timer()

        x_values.append(end_val)
        avg_insertion_time = (end - start) / (end_val - start_val)
        exec_times.append(avg_insertion_time)
    plt.title("Avg. insertion time")
    plt.xlabel("n")
    plt.ylabel("t")
    plt.plot(x_values, exec_times)
    plt.show()

def plot_avg_deletion_time(n):
    server.destroy_db()
    exec_times = []
    x_values = []
    server.destroy_db()

    insert_sorted(0, 2 ** n)

    for i in range(1, n):
        start_val = 2 ** (i-1)
        end_val = 2 ** i

        start = timeit.default_timer()
        for j in range(start_val, end_val):
            server.delete(j)
        end = timeit.default_timer()

        x_values.append(end_val)
        avg_deletion_time = (end - start) / (end_val - start_val)
        exec_times.append(avg_deletion_time)
    plt.title("Avg. deletion time")
    plt.xlabel("n")
    plt.ylabel("t")
    plt.plot(x_values, exec_times)
    plt.show()

def plot_membership_witness_size(n):
    server.destroy_db()
    x_values = []

    insert_sorted(0, n)

    witness_lenghts = []
    for i in range(0, n):
        witness_lenghts.append(len(server.get_membership_proof(i)))
        x_values.append(i)

    plt.title("Membership proof length")
    plt.xlabel("n")
    plt.ylabel("l")
    plt.plot(x_values, witness_lenghts)
    plt.show()

def plot_non_membership_witness_size(n):
    server.destroy_db()
    x_values = []

    insert_sorted(-20, 0)

    witness_lenghts = []
    for i in range(0, n):
        proof = server.get_non_membership_proof(i)
        witness_lenghts.append(len(proof))
        x_values.append(i)

    plt.title("Non-membership proof length")
    plt.xlabel("n")
    plt.ylabel("l")
    plt.plot(x_values, witness_lenghts)
    plt.show()

#plot_avg_insertion_time(15)
#plot_avg_deletion_time(15)
#plot_membership_witness_size(1000)
#plot_non_membership_witness_size(1000)
plot_avg(22000, 10, server.insert)