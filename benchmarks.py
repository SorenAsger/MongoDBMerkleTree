import random

from db_adapters import MongoDB
from auth_db_server import AuthDBServer

server = AuthDBServer(MongoDB())


def insert_many(n):
    for i in range(0, n):
        server.insert(random.randint(0, n))
    server.print_db()


def insert_sorted(n):
    for i in range(0, n):
        server.insert(i)
    print("bef", server.contains(4))
    server.print_tree()
    node = server.delete(4)

    print("aft", server.contains(4))
    server.print_tree()
    #server.print_db()

def spec():
    list = [i for i in range(0,1000)]
    random.shuffle(list)
    for x in list:
        server.insert(x)

    rand = []
    while len(rand) < 500:
        new_int = random.randint(0,1000)
        if new_int not in rand:
            rand.append(new_int)
            
    for i in range(0,500):
        server.delete(rand[i])

    server.print_tree()


server.destroy_db()
spec()
#insert_sorted(7)


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