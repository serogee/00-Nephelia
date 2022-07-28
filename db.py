import sqlite3

connections = dict()

def connect(database, *args, **kwargs):
    if database in connection:
        return connection[database]
    connections[database] = conn = sqlite3.connect(database=database, *args, **kwargs)
    return conn: sqlite3.connect