import BaseHTTPServer
import urlparse
import re
from signal import signal, SIGINT, SIGTERM
from sys import exit
import logging
import sqlite3

# Used for control interface
from threading import Thread
import threading
import socket, sys
import shlex
import copy

# Control-related variables
CONTROL_PORT = 7770
CONTROL_HOST = '127.0.0.1'
MAX_COMMAND_LENGTH = 4096
shutdownRequested = False

PORT=8880
FORM_PATH="Shorten.html"

# This should be set based on your domain, and omit the trailing `/`.
DOMAIN_PREFIX = "https://hq6.me/u"

class KeyExistError(Exception):
    pass

# This class is thread-safe. It serves reads from memory and writes
# persistently to disk before returning.
class SqliteBackedKVStore(object):
    def __init__(self, dbPath="Shortener.db", table="short_url_to_url", keyCol="shortUrl", valueCol="longUrl"):
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


class ShortenURLHandler(BaseHTTPServer.BaseHTTPRequestHandler, object):
    # Map short URL suffix to full URL
    shortUrlMap = SqliteBackedKVStore()
    nextGenerated = 1
    def __init__(self, *args, **kwargs):
        super(ShortenURLHandler, self).__init__(*args, **kwargs)

    def log_message(self, fmtstr, *args):
      logging.info("%s - - [%s] %s" %
                         (self.client_address[0],
                          self.log_date_time_string(),
						  fmtstr%args))

    # Note that the shortUrl parameter is a preference.
    @staticmethod
    def shorten(fullUrl, shortUrl = None):
      # Allow only alphanumeric URLs
      if shortUrl:
          shortUrl = re.sub("[\W_]+", '', shortUrl)
      else:
          shortUrl = str(ShortenURLHandler.nextGenerated)
          ShortenURLHandler.nextGenerated += 1

      success = False
      while not success:
        try:
          ShortenURLHandler.shortUrlMap[shortUrl] = fullUrl
          success = True
        except KeyExistError:
          # On failure, try with generated URLs until success.
          shortUrl = str(ShortenURLHandler.nextGenerated)
          ShortenURLHandler.nextGenerated += 1
          success = False
      return shortUrl


    # This assumes that the return code is 200.
    def write_response(self, response = "", content_type = "text/plain"):
      self.send_response(200);
      self.send_header("Content-Type", content_type)
      self.send_header("Content-Length", len(response))
      self.end_headers()
      self.wfile.write(response)

    def do_GET(self):
      path = self.path.lstrip("/")
      resp = None
      logging.debug("Received request for path: " +  path)
      if path in ShortenURLHandler.shortUrlMap:
        resp = ShortenURLHandler.shortUrlMap[path]
        self.send_response(302)
        self.send_header("Location", resp)
        self.end_headers()
      else:
        createForm = None
        try:
          createForm = open(FORM_PATH,  'rb').read()
        except IOError:
          self.send_error(404, "File not found")
          return
        self.write_response(createForm, "text/html")

    def do_POST(self):
      contentLength = int(self.headers.getheader('Content-Length', 0))
      postBody = self.rfile.read(contentLength)
      parsedBody = urlparse.parse_qs(postBody)

      fullUrl = None
      try:
         fullUrl = parsedBody['fullUrl'][0]
      except KeyError:
         pass

      if not fullUrl:
          self.write_response()
          return

      if not fullUrl.startswith("http"):
        fullUrl = "http://" + fullUrl

      shortUrl = None
      if 'desiredShortUrl' in parsedBody:
          shortUrl = parsedBody['desiredShortUrl'][0]

      shortUrl = ShortenURLHandler.shorten(fullUrl, shortUrl)

      # Send response
      self.write_response("%s/%s" % (DOMAIN_PREFIX.rstrip('/'), shortUrl))

def run(server_class=BaseHTTPServer.HTTPServer,
        handler_class=BaseHTTPServer.BaseHTTPRequestHandler):
    server_address = ('', PORT)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

def startControlInterface():
    def handle(clientsocket):
        print "Client connected to control interface..."
        clientsocket.settimeout(1)
        clientsocket.send(">")
        promptSent = True
        sentOutput = True
        global shutdownRequested
        while not shutdownRequested:
          try:
            if not promptSent:
              if sentOutput:
                clientsocket.send("\n")
              clientsocket.send(">")
              promptSent = True
            buf = clientsocket.recv(MAX_COMMAND_LENGTH)
            buf = buf.strip()
            # Ignore empty lines
            if buf == '':
               promptSent = False
               continue

            # Assume that commands send output unless they specify otherwise.
            sentOutput = True
            argv = shlex.split(buf)
            cmd = argv[0].lower()
            if cmd == 'exit':
                print "Client disconnected from control interface..."
                clientsocket.close()
                return
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
                clientsocket.send(controlCommands)
            elif cmd == 'add':
                output = ""
                if len(argv) < 2:
                    output = "Usage: add <fullUrl> [shortUrl]"
                elif len(argv) == 2:
                    output = ShortenURLHandler.shorten(argv[1])
                else:
                    output = ShortenURLHandler.shorten(argv[1], argv[2])
                clientsocket.send(output)
            elif cmd == 'del':
                if len(argv) < 2:
                    clientsocket.send("Usage: del <shortUrl>")
                else:
                    del ShortenURLHandler.shortUrlMap[argv[1]]
                    sentOutput = False
            elif cmd == 'get':
                output = ""
                if len(argv) < 2:
                    output = "Usage: get <shortUrl>"
                elif argv[1] not in ShortenURLHandler.shortUrlMap:
                    output = "Key '%s' not found." % argv[1]
                else:
                    output = ShortenURLHandler.shortUrlMap[argv[1]]
                clientsocket.send(output)
            elif cmd == 'list' or cmd == "ls":
                output = []
                d = ShortenURLHandler.shortUrlMap.snapshot()
                for key in d:
                  if len(argv) > 1 and argv[1] == "-l":
                    output.append(key + " : " + d[key])
                  else:
                    output.append(key)
                clientsocket.send("\n".join(output))
            else:
                clientsocket.send("Unrecognized command '%s'" % buf)
            promptSent = False
          except socket.timeout:
            pass
    def accept_commands():
        global shutdownRequested
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversocket.bind((CONTROL_HOST, CONTROL_PORT))
        serversocket.listen(10)

        # This is necessary to allow clean shutdowns
        serversocket.settimeout(1)
        while not shutdownRequested:
          try:
            (clientsocket, address) = serversocket.accept()
            handler_thread = Thread(target=handle, args=(clientsocket,))
            handler_thread.start()
          except socket.timeout:
            pass

    thread = Thread(target=accept_commands)
    thread.start()

def main():
    # Set up signal handlers
    def handler(signum, frame):
        global shutdownRequested
        shutdownRequested = True
        print "Exiting due to signal %d." % signum
        exit(0)

    signal(SIGINT, handler)
    signal(SIGTERM, handler)

	# Set up logging
    logging.basicConfig(level=logging.INFO)

    # Set up a control interface on a separate thread that we can telnet to and
    # issue commands.
    startControlInterface()

    # Start the web server
    run(BaseHTTPServer.HTTPServer, ShortenURLHandler);

if __name__ == "__main__":
	main()
