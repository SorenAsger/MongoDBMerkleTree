import matplotlib.pyplot as plt


def read_RSA_benchmarks(idx):
    f = open("rsa_benchmarks.txt", "r")
    text = f.read().split("--START RSA BENCHMARK--\n")
    measurements = text[idx].replace("(", "").replace(")", "")
    f.close()
    return get_measurements(measurements)


def read_merkle_benchmarks(idx=1):
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


class RSAMeasurements():

    def __init__(self, insertion_times, k, memqueries_proof_times, memqueries_verify_times, nonmemqueries_proof_times,
                 nonmemqueries_verify_times, nonmemwit_size, ns, sec):
        self.sec = sec
        self.insertions = ns
        self.nonmemwit_size = nonmemwit_size
        self.nonmemqueries_verify_times = nonmemqueries_verify_times
        self.nonmemqueries_proof_times = nonmemqueries_proof_times
        self.memqueries_verify_times = memqueries_verify_times
        self.memqueries_proof_times = memqueries_proof_times
        self.avg_hash_size = k
        self.insertion_times = insertion_times
        self.bulk_measurements = []
        self.deletion_times = []


def get_measurements(measurements):
    ns = []
    memqueries_proof_times = []
    memqueries_verify_times = []
    nonmemqueries_proof_times = []
    nonmemqueries_verify_times = []
    insertion_times = []
    memwit_size = []
    nonmemwit_size = []
    bulk_measurements = [[] for _ in range(16)]
    deletion_times = []
    verify_extra = 100
    reps = 5
    for measurement_no_split in measurements.split("\n")[:-1]:
        measurement = measurement_no_split.split(",")
        ns.append(int(measurement[0]))
        queries = int(measurement[1])
        k = float(measurement[11])
        sec = int(measurement[10])
        memqueries_proof_times.append(float(measurement[3]) / queries)
        memqueries_verify_times.append(float(measurement[4]) / int(measurement[1]) * reps / (reps * (1 + verify_extra)))
        nonmemqueries_proof_times.append(float(measurement[6]) / int(measurement[1]))
        nonmemqueries_verify_times.append(
            float(measurement[7]) / int(measurement[1]) * reps / (reps * (1 + verify_extra)))
        insertion_times.append(float(measurement[8]))
        memwit_size.append(float(measurement[12]))
        nonmemwit_size.append(float(measurement[13]))
        deletion_times.append(float(measurement[55]))
        measurement2 = measurement_no_split.split("[")
        bulk_times = []
        for arrays in measurement2[1:]:
            arrays = arrays.split("]")[0]
            narray = [float(x) for x in arrays.split(',')[:-1]]
            bulk_times.append(sum(narray) / len(narray))
        for i in range(len(bulk_times)):
            bulk_measurements[i].append(bulk_times[i])

    measurementObject = RSAMeasurements(insertion_times, k, memqueries_proof_times, memqueries_verify_times,
                                        nonmemqueries_proof_times,
                                        nonmemqueries_verify_times, nonmemwit_size, ns, sec)
    measurementObject.bulk_measurements = bulk_measurements
    measurementObject.deletion_times = deletion_times
    return measurementObject


def make_plots():
    measurement40 = read_RSA_benchmarks(1)
    measurement80 = read_RSA_benchmarks(2)
    measurement402 = read_RSA_benchmarks(3)
    measurement802 = read_RSA_benchmarks(4)
    merkle_measure = read_merkle_benchmarks()
    benchmark_results = "merkleVSRSA/"

    def update_insert_times(times):
        interval = 10000
        new_times = []
        for i in range(0, len(times)):
            if i > 1:
                new_times.append((times[i] - times[i - 1]) / (interval))
            else:
                new_times.append((times[i] / (interval)))
        return new_times

    # Plot insertion
    xs = [n + 10000 for n in merkle_measure[0]]
    plt.title("Avg. insertion time")
    plt.xlabel("Total insertions")
    plt.ylabel("Time in seconds")
    plt.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    # avg for 0-10k 10-20k and so on.
    # plt.plot(uns, update_insert_times(measurement40.insertion_times), label="hash40")
    print(xs)
    print(measurement80.insertions)
    plt.plot(xs, update_insert_times(measurement80.insertion_times), label="RSA-hash80")
    plt.plot(xs, merkle_measure[1], label="Merkle")
    # plt.plot(uns, update_insert_times(measurement402.insertion_times), '--',label="No-u-hash40")
    # plt.plot(uns, update_insert_times(measurement802.insertion_times), '--',label="No-u-hash80")
    plt.legend(loc="upper left")
    plt.savefig(benchmark_results + "VSinsertion_times.png")
    plt.show()

    plt.title("Avg. deletion time")
    plt.xlabel("Total insertions")
    plt.ylabel("Time in seconds")
    plt.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    # avg for 0-10k 10-20k and so on.
    # plt.plot(uns, update_insert_times(measurement40.insertion_times), label="hash40")
    plt.plot(xs, update_insert_times(measurement80.deletion_times), label="RSA-hash80")
    plt.plot(xs, merkle_measure[2][::-1], label="Merkle")
    # plt.plot(uns, update_insert_times(measurement402.insertion_times), '--',label="No-u-hash40")
    # plt.plot(uns, update_insert_times(measurement802.insertion_times), '--',label="No-u-hash80")
    plt.legend(loc="upper left")
    plt.savefig(benchmark_results + "VSDeletion_times.png")
    plt.show()

    # WitGen is compared differently

    # WitVer

    plt.title("Avg. membership witness verification time")
    plt.xlabel("Total insertions")
    plt.ylabel("Time in seconds")
    plt.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    # avg for 0-10k 10-20k and so on.
    # plt.plot(uns, update_insert_times(measurement40.insertion_times), label="hash40")
    plt.plot(xs, measurement80.memqueries_verify_times, label="RSA-hash80")
    plt.plot(xs, merkle_measure[4], label="Merkle")
    # plt.plot(uns, update_insert_times(measurement402.insertion_times), '--',label="No-u-hash40")
    # plt.plot(uns, update_insert_times(measurement802.insertion_times), '--',label="No-u-hash80")
    plt.legend(loc="upper left")
    plt.savefig(benchmark_results + "VSMembership_Verification_times.png")
    plt.show()

    # NonMem
    plt.title("Avg. non-membership witness verification time")
    plt.xlabel("Total insertions")
    plt.ylabel("Time in seconds")
    plt.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    # avg for 0-10k 10-20k and so on.
    # plt.plot(uns, update_insert_times(measurement40.insertion_times), label="hash40")
    plt.plot(xs, measurement80.nonmemqueries_verify_times, label="RSA-hash80")
    plt.plot(xs, merkle_measure[6], label="Merkle")
    # plt.plot(uns, update_insert_times(measurement402.insertion_times), '--',label="No-u-hash40")
    # plt.plot(uns, update_insert_times(measurement802.insertion_times), '--',label="No-u-hash80")
    plt.legend(loc="upper left")
    plt.savefig(benchmark_results + "VSNonMembership-Verification_times.png")
    plt.show()

    # Compare sizes???


make_plots()
