import unittest, os, gc
from SqliteKVStore import SqliteKVStore, KeyExistError

import string, random
import timeit

def generateRandomString(size=6, chars=string.ascii_uppercase + string.digits):
  return ''.join(random.choice(chars) for _ in range(size))

class TestSqliteKVStore(unittest.TestCase):
  def setUp(self):
    self.dbfile = "/tmp/testshortener.db"
    self.sql = SqliteKVStore(self.dbfile)

  def tearDown(self):
    os.remove(self.dbfile)

  def assignKeyToValue(self, key, value):
    self.sql[key] = value

  def test_get(self):
    self.assignKeyToValue("Key", "Value")
    # Get a non-existent key
    self.assertRaises(KeyError, lambda: self.sql["NonExistentKey"])
    # Get an existing key
    self.assertEquals(self.sql["Key"], "Value")

  def test_set(self):
    self.assignKeyToValue("Key", "Value")
    self.assertRaises(KeyExistError, lambda: self.assignKeyToValue("Key", "Value"))

  def test_delete(self):
    self.assignKeyToValue("Key", "Value")
    self.sql["Key"]
    self.assertRaises(KeyExistError, lambda: self.assignKeyToValue("Key", "Value"))
    del self.sql["Key"]
    self.assertRaises(KeyError, lambda: self.sql["Key"])
    # No error after deletion
    self.assignKeyToValue("Key", "Value")

  def test_persistence(self):
    self.assignKeyToValue("Key", "Value")
    self.assignKeyToValue("Key2", "Value2")
    self.sql = None
    gc.collect()
    self.sql = SqliteKVStore(self.dbfile)
    self.sql["Key"]
    self.assertRaises(KeyExistError, lambda: self.assignKeyToValue("Key", "Value"))
    del self.sql["Key"]
    self.sql = None
    gc.collect()
    self.sql = SqliteKVStore(self.dbfile)
    self.assertRaises(KeyError, lambda: self.sql["Key"])
    self.sql["Key2"]

if __name__ == '__main__':
  unittest.main()
