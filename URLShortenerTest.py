import unittest, os
from URLShortener import URLShortener

import string, random

def generateRandomString(size=6, chars=string.ascii_uppercase + string.digits):
  return ''.join(random.choice(chars) for _ in range(size))

class TestURLShortener(unittest.TestCase):
  def setUp(self):
    self.dbfile = "/tmp/testshortener.db"
    self.shortener = URLShortener(self.dbfile)
  def tearDown(self):
    os.remove(self.dbfile)
  def test_shorten(self):
    shortUrl = self.shortener.shorten("https://example.com")
    self.assertEqual(shortUrl, '1')
    shortUrl = self.shortener.shorten("https://example.com")
    self.assertEqual(shortUrl, '2')
    shortUrl = self.shortener.shorten("https://example.com", "example")
    self.assertEqual(shortUrl, 'example')
    shortUrl = self.shortener.shorten("https://example.com", "example")
    self.assertEqual(shortUrl, '3')

  def test_get(self):
    fullUrl = "https://example.com"
    shortUrl = self.shortener.shorten(fullUrl)
    self.assertEqual(self.shortener.get(shortUrl), fullUrl)

    fullUrl = "https://example2.com"
    shortUrl = self.shortener.shorten(fullUrl)
    self.assertEqual(self.shortener.get(shortUrl), fullUrl)

  def test_remove(self):
    fullUrl = "https://example.com"
    shortUrl = self.shortener.shorten(fullUrl)
    self.assertTrue(shortUrl in self.shortener.shortUrlMap)
    self.shortener.remove(shortUrl)
    self.assertFalse(shortUrl in self.shortener.shortUrlMap)

  def test_list(self):
    NUM_URLS = 6
    fullUrls = [generateRandomString() for x in range(NUM_URLS)]
    shortUrls = [self.shortener.shorten(x) for x in range(NUM_URLS)]
    listing = self.shortener.list()
    self.assertEqual(len(listing), NUM_URLS)
    self.assertTrue(all(x in listing for x in shortUrls))

  def test_handleCommand(self):
    def handle(cmd):
      return self.shortener.handleCommand(cmd)
    exit_out = handle("exit")
    self.assertEqual(exit_out, False)

    add_out = handle("add")
    self.assertEqual(add_out, "Usage: add <fullUrl> [shortUrl]")

    add_out = handle("add myfullUrl")
    self.assertEqual(add_out, '1')

    get_out = handle("get")
    self.assertEqual(get_out, 'Usage: get <shortUrl>')

    get_out = handle("get 2")
    self.assertEqual(get_out, "Key '2' not found.")

    get_out = handle("get 1")
    self.assertEqual(get_out, "myfullUrl")

    del_out = handle("del")
    self.assertEqual(del_out, 'Usage: del <shortUrl>')

    del_out = handle("del 1")
    self.assertEqual(del_out, "")

    surl1 = self.shortener.shorten("foo")
    surl2 = self.shortener.shorten("bar")
    list_out = handle("list")
    self.assertTrue(all(str(x) in list_out for x in [surl1,surl2]))

    list_out = handle("list -l")
    self.assertTrue(all(str(x) in list_out for x in [2,3, "foo", "bar"]))


if __name__ == '__main__':
  unittest.main()
