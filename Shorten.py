import BaseHTTPServer
import urlparse
import re
from signal import signal, SIGINT, SIGTERM
from sys import exit
import logging

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

def main():
    # Set up signal handlers
    def handler(signum, frame):
        print "Exiting due to signal %d." % signum
        exit(0)
    signal(SIGINT, handler)
    signal(SIGTERM, handler)

	# Set up logging
    logging.basicConfig(level=logging.INFO)

    run(BaseHTTPServer.HTTPServer, ShortenURLHandler);

if __name__ == "__main__":
	main()
