import random

from DBManagement import MongoDB
from authdbserver import AuthDBServer

server = AuthDBServer(MongoDB())


def insert_many(n):
    for i in range(0, n):
        server.insert(random.randint(0, n))
    server.print_db()


def insert_sorted(n):
    for i in range(0, n):
        server.insert(i)
    server.print_db()

server.destroy_db()
insert_sorted(40)

'''
exec_times = []
x_values = []
server.destroy_db()

for i in range(1, 8):
    x = 2 ** i

    start = timeit.default_timer()
    insert_sorted(x)
    end = timeit.default_timer()

    x_values.append(x)
    exec_times.append((end - start) / math.log(x))


print(x_values)
print(exec_times)
plt.plot(x_values, exec_times)
plt.show()
'''