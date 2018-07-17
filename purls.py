#!/usr/bin/env python

import BaseHTTPServer
import urlparse
import re
from signal import signal, SIGINT, SIGTERM
from sys import exit
import logging

# Actual shortener
from URLShortener import URLShortener

# Option parsing
from docopt import docopt

# Used for control interface
from threading import Thread
import threading
import socket, sys

# Hardcoded constants
FORM_PATH="Shorten.html"
CONTROL_HOST = '127.0.0.1'
MAX_COMMAND_LENGTH = 4096

# Used for synchronization between signal handlers are all other threads.
shutdownRequested = False

# Used to output the appropriate prefix for shortened URLs.
DOMAIN_PREFIX = "https://hq6.me/u"

# The object performing the shorten operations.
shortener = None

class ShortenURLHandler(BaseHTTPServer.BaseHTTPRequestHandler, object):
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
      logging.debug("Received request for path: " +  path)
      fullUrl = shortener.get(path)
      if fullUrl:
        self.send_response(302)
        self.send_header("Location", fullUrl)
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

      shortUrl = shortener.shorten(fullUrl, shortUrl)

      # Send response
      self.write_response("%s/%s" % (DOMAIN_PREFIX.rstrip('/'), shortUrl))

def run(server_class, handler_class, port):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

def startControlInterface(controlPort):
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
            output = shortener.handleCommand(buf)
            # This is an explicit check for False because we do not want to
            # interpret the empty string as False.
            if output == False:
              clientsocket.close()
              return
            if output != "":
              clientsocket.send(output)
              sentOutput = True
            else:
              sentOutput = False
            promptSent = False
          except socket.timeout:
            pass
    def accept_commands():
        global shutdownRequested
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversocket.bind((CONTROL_HOST, controlPort))
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

doc = r"""
purls.py: Personal URL shortener, to run on your own domain, subdomain, or
custom path. Specify DOMAIN_PREFIX as the prefix of your shortened URLs,
starting with the http or https.

Usage: ./purls.py [-h] [-p <port>] [-c <controlport>] [-s <dbfile>] DOMAIN_PREFIX

    -h,--help                show this
    -p,--port <port>         specify the port that this Shortener should run on [default: 8880]
    -c,--controlport <port>  specify the port that command shell should run on [default: 7770]
    -s,--sqlite <dbfile>     specify the filename of the sqlite3 database file [default: Shortener.db]
"""

def main():
	# Examine options
    options = docopt(doc)
    global DOMAIN_PREFIX, shortener
    DOMAIN_PREFIX = options['DOMAIN_PREFIX']
    port = int(options['--port'])
    controlPort = int(options['--controlport'])
    dbfile = options['--sqlite']

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

    # Instantiate the shortener
    shortener = URLShortener(dbfile)

    # Set up a control interface on a separate thread that we can telnet to and
    # issue commands.
    startControlInterface(controlPort)

    # Print diagnostic information
    print "purls serving\n\tDB File: %s\n\tServing Port: %d\n\tDomain Prefix: %s\n\tControl Port: %d" % (dbfile, port, DOMAIN_PREFIX, controlPort)

    # Start the web server
    run(BaseHTTPServer.HTTPServer, ShortenURLHandler, port);

if __name__ == "__main__":
	main()
