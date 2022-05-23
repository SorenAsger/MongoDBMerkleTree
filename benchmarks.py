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

def get_avg_time(n, interval_length, function, inserting=True, random_writes=True):
    y_values = []
    x_values = []
    values = [random.randint(0, 2 ** 64) for _ in range(n)]
    if inserting:
        server.destroy_db()
    else:
        for val in values:
            server.insert(val)
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
    values = [random.randint(0, 2 ** 64) for _ in range(n)]
    if membership:
        proof_values = values
    else:
        proof_values = [random.randint(0, 2 ** 64) for _ in range(n)]

    # Insert interval length elements
    # get avg time to generate 100 witnesses
    # repeat until n
    for j in range(0, n, interval_length):
        for k in range(j, j+interval_length):
            server.insert(values[k])
        proofs = []
        val_idx = [random.randint(0, j + interval_length-1) for _ in range(amount_of_witnesses)]
        start = timeit.default_timer()
        for i in range(0, amount_of_witnesses):
            # all values in [0, j + interval_length
            # should be in the DB at this point in time.
            val = proof_values[val_idx[i]]
            proofs.append(proof_func(val))
        end = timeit.default_timer()
        avg_y_proof = (end - start) / amount_of_witnesses
        #random.shuffle(proofs)
        start = timeit.default_timer()
        for i in range(0, amount_of_witnesses):
            # all values in [0, j + interval_length
            # should be in the DB at this point in time.
            assert function(proof_values[val_idx[i]], proofs[i])
        end = timeit.default_timer()

        avg_y_verify = (end - start) / amount_of_witnesses

        y_values_verify.append(avg_y_verify)
        y_values_proof.append(avg_y_proof)
        x_values.append(j)

    return x_values, y_values_proof, y_values_verify


def get_avg_witness_length(n, interval_length, function, membership=True):
    y_values = []
    x_values = []
    amount_of_witnesses = 1000

    for j in range(1, n, interval_length):
        insert_sorted(j, j + interval_length)
    server.destroy_db()
    values = [random.randint(0, 2 ** 64) for _ in range(n + 1)]
    for j in range(0, n, interval_length):

        for k in range(j, j+interval_length):
            server.insert(values[k])

        length = 0
        for i in range(0, amount_of_witnesses):
            if membership:
                val_idx = random.randint(0, j + interval_length-1)
                val = values[val_idx]
            else:
                val = random.randint(0, 2**64)  # unlikely to be same as previous elements
            result = function(val)
            if result is not None:
                length += str(result).__sizeof__()
            else:
                print(membership, "got none THIS SHOULD NOT HAPPEN")

        avg_y = length / amount_of_witnesses
        y_values.append(avg_y)
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
    vals = [[res[i][j]/reps for j in range(len(res[i]))] for i in range(len(res))]
    for _ in range(reps - 1):
        res = experiment()
        for j in range(len(res)):
            for i in range(len(res[j])):
                vals[j][i] = vals[j][i] + res[j][i]/reps
    return tuple(vals)


server.destroy_db()
n = 100000
interval = 5000
ma = 1
time_label = "seconds"
length_label = "bytes"


#x_vals, y_vals = get_avg_time(n, interval, server.insert, random_writes=True)
#plot(x_vals, y_vals, "Avg. insertion time", "total values in DB", time_label, ma, filename="bench2")


x_vals, y_proof, y_verify = repeat_and_average_experiment(lambda: get_avg_witness_time(n, interval, verifier.verify_membership_proof, server.get_membership_proof))
plot(x_vals, y_proof, "Avg. membership witness generation time", "total values in DB", time_label, ma,
     filename="wit_gen_time")

plot(x_vals, y_verify, "Avg. membership witness verification time", "total values in DB", time_label, ma,
     filename="wit_ver_time")

x_vals, y_vals = repeat_and_average_experiment(lambda: get_avg_witness_length(n, interval, server.get_non_membership_proof, membership=False))
plot(x_vals, y_vals, "Avg. non-membership witness length", "total values in DB", length_label, ma_weight=1,
     scientific_y=False, filename="wit_length")



x_vals, y_proof, y_verify = repeat_and_average_experiment(lambda: get_avg_witness_time(n, interval, verifier.verify_non_membership_proof, server.get_non_membership_proof, membership=False))
plot(x_vals, y_proof, "Avg. non-membership witness generation time", "total values in DB", time_label, ma,
     filename="non_mem_wit_gen_time")

plot(x_vals, y_verify, "Avg. non-membership witness verification time", "total values in DB", time_label, ma,
     filename="non_mem_wit_ver_time")




x_vals, y_vals = repeat_and_average_experiment(lambda: get_avg_time(n, interval, server.insert))
plot(x_vals, y_vals, "Avg. insertion time", "total values in DB", time_label, ma, filename="insertion")

x_vals, y_vals = repeat_and_average_experiment(lambda: get_avg_time(n, interval, server.delete, inserting=False))
plot(x_vals, y_vals[::-1], "Avg. deletion time", "total values in DB", time_label, ma, filename="deletion")



x_vals, y_vals = repeat_and_average_experiment(lambda: get_avg_witness_length(n, interval, server.get_membership_proof))
plot(x_vals, y_vals, "Avg. membership witness length", "total values in DB", length_label, ma_weight=1,
     scientific_y=False, filename="wit_length")

#server = ImmuServer()
#server.setdb("insert name here")
#    |
#    |    Immu benchmark for memberships
#    V
'''
x_vals, y_vals = get_avg_witness_time(n, interval, server.get_membership_proof)
plot(x_vals, y_vals, "Avg. membership verification time (ImmuDB)", "total values in DB", time_label, ma, filename="immu")
'''




