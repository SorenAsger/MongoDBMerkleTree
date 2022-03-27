import cProfile
import random

from DBManagement import MongoDB
from auth_db_server import auth_db_server

server = auth_db_server(MongoDB())

def insertmany():
    for i in range(0, 1000):
        server.insert(random.randint(0, 10000))
    server.print_db()

def insert_sorted():
    for i in range(0, 1000):
        server.insert(i)
    server.print_db()

server.destroy_db()
server.print_db()
insert_sorted()
#cProfile.run('insert_sorted()')
