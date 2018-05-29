import BaseHTTPServer
import urlparse

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

    def do_GET(self):
      path = self.path.lstrip("/")
      resp = None
      print path
      print  ShortenURLHandler.shortUrlMap
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
        self.send_response(200);
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", len(createForm))
        self.end_headers()
        self.wfile.write(createForm)

    def do_POST(self):
      contentLength = int(self.headers.getheader('Content-Length', 0))
      postBody = self.rfile.read(contentLength)
      parsedBody = urlparse.parse_qs(postBody)

      # TODO: Make the naming consistent
      fullUrl = parsedBody['longUrl'][0]
      shortUrl = None
      if 'desiredShortUrl' in parsedBody:
          shortUrl = parsedBody['desiredShortUrl'][0]
      else:
          shortUrl = str(ShortenURLHandler.nextGenerated)
          ShortenURLHandler.nextGenerated += 1

      ShortenURLHandler.shortUrlMap[shortUrl] = fullUrl

      # Send response
      self.send_response(200);
      response = "Your Shiny New ShortURL: %s/%s" % (DOMAIN_PREFIX.rstrip('/'), shortUrl)
      self.send_header("Content-Type", "text/plain")
      self.send_header("Content-Length", len(response))
      self.end_headers()
      self.wfile.write(response)



def run(server_class=BaseHTTPServer.HTTPServer,
        handler_class=BaseHTTPServer.BaseHTTPRequestHandler):
    server_address = ('', PORT)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

if __name__ == "__main__":
    run(BaseHTTPServer.HTTPServer, ShortenURLHandler);
