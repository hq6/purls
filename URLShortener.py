from SqliteKVStore import SqliteKVStore, KeyExistError
import shlex

class URLShortener():
    def __init__(self, dbfile):
       # Map short URL suffix to full URL
       self.shortUrlMap = SqliteKVStore(dbfile)
       self.nextGenerated = 1
       pass

    # The shortUrl parameter is a preference, not a requirement.  If the given
    # shortURL is alraedy taken, a numerical shortURL will be assigned.
    def shorten(self, fullUrl, shortUrl = None):
      # Allow only alphanumeric URLs
      if shortUrl:
          shortUrl = re.sub("[\W_]+", '', shortUrl)
      else:
          shortUrl = str(self.nextGenerated)
          self.nextGenerated += 1

      success = False
      while not success:
        try:
          self.shortUrlMap[shortUrl] = fullUrl
          success = True
        except KeyExistError:
          # On failure, try with generated URLs until success.
          shortUrl = str(self.nextGenerated)
          self.nextGenerated += 1
          success = False
      return shortUrl

    def remove(self, shortUrl):
      del self.shortUrlMap[shortUrl]

    def get(self, path):
      if path in self.shortUrlMap:
        return self.shortUrlMap[path]
      return None

    def list(self):
      return self.shortUrlMap.snapshot()
