from immudb import ImmudbClient

class ImmuServer:

    def __init__(self, insert_limit=1000):
        self.client = ImmudbClient()
        self.client.login("immudb", "immudb")
        self.values = []
        self.insert_limit = insert_limit

    def insert(self, value):
        self.values.append(value)
        if len(self.values) >= self.insert_limit:
            self.insert_current()
        self.client.set(b"%x" % value, b"%x" % value)

    def insert_limited_write(self, value):
        self.values.append(value)
        if len(self.values) >= self.insert_limit:
            self.insert_current()

    def insert_current(self):
        to_insert = {}
        for value in self.values:
            to_insert[b"%x" % value] = b"%x" % value
        self.client.setAll(to_insert)
        self.values = []

    def get_membership_proof(self, value):
        if len(self.values) > 0:
            print("Inserting ", len(self.values))
            self.insert_current()
        return self.client.verifiedGet(b"%x" % value)

    def setdb(self, dbname):
        self.name = dbname
        self.client.databaseCreate(dbname)
        self.client.databaseUse(dbname)

    def destroy_db(self):
        self.setdb(self.name + "1")
