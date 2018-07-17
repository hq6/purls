import sqlite3
import threading
import copy

class KeyExistError(Exception):
    pass
# This class is thread-safe. It serves reads from memory and writes
# persistently to disk before returning.
class SqliteKVStore(object):
    def __init__(self, dbPath="Shortener.db", table="short_url_to_url", keyCol="shortUrl", valueCol="fullUrl"):
       self.mutex = threading.Lock()
       self.dbPath = dbPath
       self.table = table
       self.keyCol = keyCol
       self.valueCol = valueCol

       with self.mutex:
         self.inMemoryMap = {}
         self.db = sqlite3.connect(dbPath, check_same_thread=False)
         self.db.row_factory = sqlite3.Row
         c = self.db.cursor()
         c.execute("CREATE TABLE IF NOT EXISTS {} ({} TEXT PRIMARY KEY, {} TEXT)".format(table, keyCol, valueCol))
         # Read inMemoryMap out of the db
         rows = c.execute('SELECT "{}" as key, "{}" as value from "{}"'.format(keyCol, valueCol, table))
         for row in rows:
            self.inMemoryMap[row["key"]] = row["value"]

    def __getitem__(self, key):
      with self.mutex:
        return self.inMemoryMap[key]

    def __contains__(self, key):
      with self.mutex:
        return key in self.inMemoryMap

    # This will insert but not update; should raise a KeyExistError if the key
    # already exists
    def __setitem__(self, key, val):
      with self.mutex:
        c = self.db.cursor()
        try:
          c.execute("INSERT INTO {} ({}, {}) VALUES(?, ?)".format(self.table, self.keyCol, self.valueCol), (key, val))
          self.db.commit()
        except sqlite3.IntegrityError:
          raise KeyExistError
        # Write to in-memory map only if the db write succeeded.
        self.inMemoryMap[key] = val

    def __delitem__(self, key):
      with self.mutex:
        c = self.db.cursor()
        c.execute("DELETE FROM {} WHERE {} = ?".format(self.table, self.keyCol), (key,))
        self.db.commit()
        try:
          del self.inMemoryMap[key]
        except KeyError:
          pass

    def snapshot(self):
      with self.mutex:
        # We make a copy here to avoid racing with a concurrent modification.
        return copy.deepcopy(self.inMemoryMap)
