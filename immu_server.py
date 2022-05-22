from immudb import ImmudbClient

class ImmuServer:

    def __init__(self):
        self.client = ImmudbClient()
        self.client.login("immudb", "immudb")

    def insert(self, value):
        self.client.set(b"%x" % value, b"%x" % value)

    def get_membership_proof(self, value):
        self.client.verifiedGet(b"%x" % value)

    def setdb(self, dbname):
        self.client.databaseCreate(dbname)
        self.client.databaseUse(dbname)