import cProfile
import math
import sys

import numpy as np
import random
import timeit
import matplotlib.pyplot as plt
import scipy.ndimage.filters as ndif

from verifier import Verifier
from cache import Cache
from db_adapters import MongoDB
from auth_db_server import AuthDBServer

dbi = MongoDB()
cache = Cache(dbi, write_to_db=False)
server = AuthDBServer(dbi, cache)
verifier = Verifier(server)


def insert_many(start, end):
    for i in range(start, end):
        server.insert(random.randint(0, 2 ** 128))


def insert_sorted(start, end):
    for i in range(start, end):
        server.insert(i)


def moving_average(x, w):
    return np.convolve(x, np.ones(w), 'valid') / w


# cProfile.run('insert_sorted(0, 1000)')

def get_avg_time(n, interval_length, function, random_writes=False, input_factor=1):
    y_values = []
    x_values = []

    for j in range(1, n, interval_length):

        start = timeit.default_timer()
        for i in range(j, j + interval_length):
            if random_writes:
                function(input_factor * random.randint(0, 2 ** 32))
            else:
                function(i)
        end = timeit.default_timer()

        avg_y = ((end - start) / interval_length) / (1 + math.log(j))

        y_values.append(avg_y)
        x_values.append(j)

    return x_values, y_values


def get_avg_length(n, interval_length, function, input_factor=1):
    y_values = []
    x_values = []

    for j in range(1, n, interval_length):

        length = 0
        for i in range(j, j + interval_length):
            result = function(input_factor * i)
            if result is not None:
                length += sys.getsizeof(result)

        avg_y = length / interval_length
        y_values.append(avg_y)
        x_values.append(j)

    return x_values, y_values


def plot(x_values, y_values, titel, x_label, y_label, ma_weight, scientific_y=True, logy=True):
    plt.title(titel)
    plt.xlabel(x_label)
    plt.ylabel(y_label)

    if scientific_y:
        plt.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    else:
        plt.ticklabel_format(axis="y", style="plain", scilimits=(0, 0))

    y_values = moving_average(y_values, ma_weight).tolist()
    x_values = x_values[ma_weight - 1:]
    plt.plot(x_values, y_values)
    plt.show()


server.destroy_db()
n = 60000
interval = 1000
ma = 1
time_label = "seconds"

x_vals, y_vals = get_avg_time(n, interval, server.insert)
plot(x_vals, y_vals, "Avg. insertion time / log(n)", "n", time_label, ma)


x_vals, y_vals = get_avg_time(n, interval, server.get_membership_proof)
plot(x_vals, y_vals, "Avg. membership witness generation time  / log(n)", "n", time_label, ma)

x_vals, y_vals = get_avg_time(n, interval, server.get_non_membership_proof, input_factor=-1)
plot(x_vals, y_vals, "Avg. non-membership witness generation time  / log(n)", "n", time_label, ma)

x_vals, y_vals = get_avg_length(n, interval, server.get_membership_proof)
plot(x_vals, y_vals, "Avg. membership witness length  / log(n)", "n", "bytes", ma_weight=1, scientific_y=False)

x_vals, y_vals = get_avg_length(n, interval, server.get_non_membership_proof, input_factor=-1)
plot(x_vals, y_vals, "Avg. non-membership witness length  / log(n)", "n", "bytes", ma_weight=1, scientific_y=False)

x_vals, y_vals = get_avg_time(n, interval, verifier.verify_membership)
plot(x_vals, y_vals, "Avg. membership witness verification time  / log(n)", "n", time_label, ma)

x_vals, y_vals = get_avg_time(n, interval, verifier.verify_non_membership)
plot(x_vals, y_vals, "Avg. non-membership witness verification time  / log(n)", "n", time_label, ma)

x_vals, y_vals = get_avg_time(n, interval, server.delete)
plot(x_vals, y_vals, "Avg. deletion time  / log(n)", "n", "s", ma)

