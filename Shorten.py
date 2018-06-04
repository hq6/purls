import BaseHTTPServer
import urlparse
import re
from signal import signal, SIGINT, SIGTERM
from sys import exit
import logging

# Used for control interface
from threading import Thread
import socket, sys

# Control-related variables
CONTROL_PORT = 7770
CONTROL_HOST = '127.0.0.1'
MAX_COMMAND_LENGTH = 4096
shutdownRequested = False

PORT=8880
FORM_PATH="Shorten.html"

# This should be set based on your domain, and omit the trailing `/`.
DOMAIN_PREFIX = "https://hq6.me/u"

class ShortenURLHandler(BaseHTTPServer.BaseHTTPRequestHandler, object):
    # Map short URL suffix to full URL
    shortUrlMap = {}
    nextGenerated = 1
    def __init__(self, *args, **kwargs):
        super(ShortenURLHandler, self).__init__(*args, **kwargs)

    def log_message(self, fmtstr, *args):
      logging.info("%s - - [%s] %s" %
                         (self.client_address[0],
                          self.log_date_time_string(),
						  fmtstr%args))

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
          shortUrl = re.sub("[\W_]+", '', shortUrl)
      else:
          shortUrl = str(ShortenURLHandler.nextGenerated)
          ShortenURLHandler.nextGenerated += 1

      ShortenURLHandler.shortUrlMap[shortUrl] = fullUrl

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
        global shutdownRequested
        while not shutdownRequested:
          try:
            if not promptSent:
              clientsocket.send(">")
              promptSent = True
            buf = clientsocket.recv(MAX_COMMAND_LENGTH)
            buf = buf.strip()
            if buf == 'exit':
                print "Client disconnected from control interface..."
                clientsocket.close()
                return
            else:
                clientsocket.send("Unrecognized command '%s'\n" % buf)
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
