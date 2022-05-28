import cProfile
import math
import sys

import numpy as np
import random
import timeit
import matplotlib.pyplot as plt

from verifier import Verifier
from cache import Cache
from db_adapters import MongoDB
from auth_db_server import AuthDBServer
from immu_server import ImmuServer

dbi = MongoDB()
cache = Cache(dbi)
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

def get_avg_time(n, interval_length, function, inserting=True, random_writes=True):
    y_values = []
    x_values = []
    values = [random.randint(0, 2 ** 63) for _ in range(n)]
    if inserting:
        server.destroy_db()
    else:
        for val in values:
            server.insert_limited_write(val)
    for j in range(0, n, interval_length):

        start = timeit.default_timer()
        for i in range(j, j + interval_length):
            if random_writes:
                function(values[i])
            else:
                function(i)
        end = timeit.default_timer()

        avg_y = (end - start) / interval_length

        y_values.append(avg_y)
        x_values.append(j)

    return x_values, y_values


def get_avg_witness_time(n, interval_length, function, proof_func, membership=True):
    y_values_verify = []
    y_values_proof = []
    x_values = []
    amount_of_witnesses = 100
    server.destroy_db()
    values = [random.randint(0, 2 ** 63) for _ in range(n)]
    if membership:
        proof_values = values
    else:
        proof_values = [random.randint(0, 2 ** 63) for _ in range(n)]

    # Insert interval length elements
    # get avg time to generate 100 witnesses
    # repeat until n
    for j in range(0, n, interval_length):
        for k in range(j, j + interval_length):
            server.insert_limited_write(values[k])
        proofs = []
        val_idx = [random.randint(0, j + interval_length - 1) for _ in range(amount_of_witnesses)]
        start = timeit.default_timer()
        for i in range(0, amount_of_witnesses):
            # all values in [0, j + interval_length
            # should be in the DB at this point in time.
            val = proof_values[val_idx[i]]
            proofs.append(proof_func(val))
        end = timeit.default_timer()
        avg_y_proof = (end - start) / amount_of_witnesses
        y_values_proof.append(avg_y_proof)
        if function is None:
            continue
        # random.shuffle(proofs)
        start = timeit.default_timer()
        for i in range(0, amount_of_witnesses):
            # all values in [0, j + interval_length
            # should be in the DB at this point in time.
            assert function(proof_values[val_idx[i]], proofs[i])
        end = timeit.default_timer()

        avg_y_verify = (end - start) / amount_of_witnesses

        y_values_verify.append(avg_y_verify)

        x_values.append(j)

    return x_values, y_values_proof, y_values_verify


def get_avg_witness_length(n, interval_length, function, membership=True):
    y_values = []
    x_values = []
    amount_of_witnesses = 1000

    for j in range(0, n, interval_length):
        insert_sorted(j, j + interval_length)
    server.destroy_db()
    values = [random.randint(0, 2 ** 63) for _ in range(n + 1)]
    for j in range(0, n, interval_length):

        for k in range(j, j + interval_length):
            server.insert_limited_write(values[k])

        length = 0
        for i in range(0, amount_of_witnesses):
            if membership:
                val_idx = random.randint(0, j + interval_length - 1)
                val = values[val_idx]
            else:
                val = random.randint(0, 2 ** 63)  # unlikely to be same as previous elements
            result = function(val)
            if result is not None:
                length += str(result).__sizeof__()
            else:
                print(membership, "got none THIS SHOULD NOT HAPPEN")

        avg_y = length / amount_of_witnesses
        y_values.append(avg_y)
        x_values.append(j)

    return x_values, y_values


def get_avg_depth(n, interval_length):
    y_values= []
    x_values = []
    server.destroy_db()
    values = [random.randint(0, 2 ** 63) for _ in range(n)]

    # Insert interval length elements
    # get avg time to generate 100 witnesses
    # repeat until n
    for j in range(0, n, interval_length):
        for k in range(j, j + interval_length):
            server.insert_without_write(values[k])
        y_values.append(server.get_depth())
        x_values.append(j)

    return x_values, y_values



def plot(x_values, y_values, titel, x_label, y_label, ma_weight, filename, scientific_y=True, logy=True):
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
    plt.savefig("plots/" + filename)
    plt.show()


def repeat_and_average_experiment(experiment, reps=5):
    print("starting experiment", experiment.__name__)
    res = experiment()
    vals = [[res[i][j] / reps for j in range(len(res[i]))] for i in range(len(res))]
    for _ in range(reps - 1):
        res = experiment()
        for j in range(len(res)):
            for i in range(len(res[j])):
                vals[j][i] = vals[j][i] + res[j][i] / reps
    return tuple(vals)


server.destroy_db()
n = 100000
interval = 10000
ma = 1
time_label = "seconds"
length_label = "bytes"


def read_benchmarks(idx=1):
    fil = open("benchmarks.txt", 'r')
    text = fil.read().split("NEW\n")
    lines = text[idx].split("\n")
    data = []
    for line in lines[:-1]:
        line = line.replace('[', '')
        line = line.replace(']', '')
        new_data = []
        for point in line.split(","):
            new_data.append(float(point))
        data.append(new_data)
    return data


# x_vals, y_vals = get_avg_time(n, interval, server.insert, random_writes=True)
# plot(x_vals, y_vals, "Avg. insertion time", "total values in DB", time_label, ma, filename="bench2")

def make_plots(benchmarks):
    xs = [n + 10000 for n in benchmarks[0]]

    plot(xs, benchmarks[1], "Avg. insertion time", "total values in DB", time_label, ma, filename="insertion")
    plot(xs, benchmarks[2][::-1], "Avg. deletion time", "total values in DB", time_label, ma, filename="deletion")
    plot(xs, benchmarks[3], "Avg. membership witness generation time", "total values in DB", time_label, ma,
         filename="wit_gen_time")
    plot(xs, benchmarks[4], "Avg. membership witness verification time", "total values in DB", time_label, ma,
         filename="wit_ver_time")

    plot(xs, benchmarks[5], "Avg. non-membership witness generation time", "total values in DB", time_label, ma,
         filename="non_mem_wit_gen_time")
    plot(xs, benchmarks[6], "Avg. non-membership witness verification time", "total values in DB", time_label, ma,
         filename="non_mem_wit_ver_time")
    plot(xs, benchmarks[7], "Avg. membership witness length", "total values in DB", length_label, ma_weight=1,
         scientific_y=False, filename="wit_length")
    plot(xs, benchmarks[8], "Avg. non-membership witness length", "total values in DB", length_label, ma_weight=1,
         scientific_y=False, filename="wit_length")


def run_benchmarks():
    f = open("benchmarks_server.txt", 'a')
    f.write("NEW\n")
    x_vals, y_vals = repeat_and_average_experiment(lambda: get_avg_time(n, interval, server.insert_limited_write))
    plot(x_vals, y_vals, "Avg. insertion time", "total values in DB", time_label, ma, filename="insertion")
    f.write(x_vals.__str__() + "\n")
    f.write(y_vals.__str__() + "\n")

    x_vals, y_vals = repeat_and_average_experiment(
        lambda: get_avg_time(n, interval, server.delete_limited_write, inserting=False))
    plot(x_vals, y_vals[::-1], "Avg. deletion time", "total values in DB", time_label, ma, filename="deletion")
    f.write(y_vals.__str__() + "\n")

    x_vals, y_proof, y_verify = repeat_and_average_experiment(
        lambda: get_avg_witness_time(n, interval, verifier.verify_membership_proof, server.get_membership_proof))
    plot(x_vals, y_proof, "Avg. membership witness generation time", "total values in DB", time_label, ma,
         filename="wit_gen_time")
    plot(x_vals, y_verify, "Avg. membership witness verification time", "total values in DB", time_label, ma,
         filename="wit_ver_time")
    f.write(y_proof.__str__() + "\n")
    f.write(y_verify.__str__() + "\n")

    x_vals, y_proof, y_verify = repeat_and_average_experiment(
        lambda: get_avg_witness_time(n, interval, verifier.verify_non_membership_proof, server.get_non_membership_proof,
                                     membership=False))
    plot(x_vals, y_proof, "Avg. non-membership witness generation time", "total values in DB", time_label, ma,
         filename="non_mem_wit_gen_time")
    plot(x_vals, y_verify, "Avg. non-membership witness verification time", "total values in DB", time_label, ma,
         filename="non_mem_wit_ver_time")

    f.write(y_proof.__str__() + "\n")
    f.write(y_verify.__str__() + "\n")

    x_vals, y_vals = repeat_and_average_experiment(
        lambda: get_avg_witness_length(n, interval, server.get_membership_proof))
    plot(x_vals, y_vals, "Avg. membership witness length", "total values in DB", length_label, ma_weight=1,
         scientific_y=False, filename="wit_length")
    f.write(y_vals.__str__() + "\n")

    x_vals, y_vals = repeat_and_average_experiment(
        lambda: get_avg_witness_length(n, interval, server.get_non_membership_proof, membership=False))
    plot(x_vals, y_vals, "Avg. non-membership witness length", "total values in DB", length_label, ma_weight=1,
         scientific_y=False, filename="wit_length")
    f.write(y_vals.__str__() + "\n")


# make_plots(read_benchmarks())

#run_benchmarks()

def plot_avg_depth():
    x_vals, y_vals = repeat_and_average_experiment(lambda: get_avg_depth(n, interval))
    plot(x_vals, y_vals, "Avg. depth", "total values in DB", time_label, ma, filename="depth", scientific_y=False)

#server = ImmuServer()


def run_immu_benchmarks():
    f = open("immubenchmarks.txt", 'a')
    f.write("NEW\n")
    server.setdb("im")
    x_vals, y_vals = repeat_and_average_experiment(lambda: get_avg_time(n, interval, server.insert_limited_write))
    x_vals = [x + 10000 for x in x_vals]
    plot(x_vals, y_vals, "Avg. insertion time", "total values in DB", time_label, ma, filename="immuinsert")
    f.write(x_vals.__str__() + "\n")
    f.write(y_vals.__str__() + "\n")

    x_vals_a, y_vals, _ = repeat_and_average_experiment(lambda: get_avg_witness_time(n, interval, None, server.get_membership_proof))
    #print(x_vals, y_vals)
    f.write(y_vals.__str__() + "\n")
    plot(x_vals, y_vals, "Avg. membership verification time (ImmuDB)", "total values in DB", time_label, ma,
         filename="immuverify")

plot_avg_depth()
#run_immu_benchmarks()
