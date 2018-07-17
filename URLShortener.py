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

    # A string return value means future commands may come, while False means
    # that the connection should be closed.
    def handleCommand(self, commandLine):
      # Assume that commands send output unless they specify otherwise.
      argv = shlex.split(commandLine)
      cmd = argv[0].lower()
      if cmd == 'exit':
          print "Client disconnected from control interface..."
          return False
      elif cmd == 'help':
          controlCommands = """
List of commands:
  help
  exit
  add <fullUrl> [shortUrl]
  del <shortUrl>
  get <shortUrl>
  list [-l]
                """.strip()
          return controlCommands
      elif cmd == 'add':
          if len(argv) < 2:
              return "Usage: add <fullUrl> [shortUrl]"
          elif len(argv) == 2:
              return self.shorten(argv[1])
          else:
              return self.shorten(argv[1], argv[2])
      elif cmd == 'del' or cmd == "rm":
          if len(argv) < 2:
              return "Usage: del <shortUrl>"
          else:
              self.remove(argv[1])
              return ""
      elif cmd == 'get' or cmd == "cat":
          if len(argv) < 2:
              return "Usage: get <shortUrl>"
          elif not self.get(argv[1]):
              return "Key '%s' not found." % argv[1]
          else:
              return self.get(argv[1])
      elif cmd == 'list' or cmd == "ls":
          output = []
          d = self.list()
          for key in d:
            if len(argv) > 1 and argv[1] == "-l":
              output.append(key + " : " + d[key])
            else:
              output.append(key)
          return "\n".join(output)
      else:
          return "Unrecognized command '%s'" % buf
