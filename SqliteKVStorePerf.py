import unittest, os, gc
from SqliteKVStore import SqliteKVStore, KeyExistError

import string, random
import timeit

class TestSqliteKVStore(unittest.TestCase):
  def setUp(self):
    self.dbfile = "/tmp/testshortener.db"
    self.sql = SqliteKVStore(self.dbfile)

  def tearDown(self):
    os.remove(self.dbfile)

  def writeRange(self, upper):
    for x in range(upper):
      self.sql[x] = str(x)

  def clearRange(self, upper):
    for x in range(upper):
      del self.sql[x]

  def readRandom(self, upper):
    return self.sql[random.randint(0,upper - 1)]

  def test_set(self):
    NUM_RUNS = 5
    NUM_KEYS = 1000
    print
    for x in range(NUM_RUNS):
      print "%d writes per second" % (NUM_KEYS / timeit.timeit(lambda : self.writeRange(NUM_KEYS), \
          lambda: self.clearRange(NUM_KEYS), number = 1))

  def test_get(self):
    NUM_RUNS = 5
    NUM_KEYS = 1000
    NUM_QUERIES = 1000
    print
    self.writeRange(NUM_KEYS)

    timings = []
    for x in range(NUM_RUNS):
      timings.append(timeit.timeit(lambda : self.readRandom(NUM_KEYS), number = NUM_QUERIES))

    print "\n".join(["%d reads per second" % (NUM_QUERIES / x) for x in timings])

if __name__ == '__main__':
  unittest.main()
