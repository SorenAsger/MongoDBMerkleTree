import cProfile
import random

def insertmany(self):
    for i in range(0, 1000):
        self.insert(random.randint(0, 10000))
    self.print_db()

def insert_sorted(self):
    for i in range(0, 100):
        self.insert(i)
    self.print_db()

cProfile.run('insert_sorted()')