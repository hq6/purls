## Minimal URL Shortener

This URL shortener is designed to run either on its own web server or behind an
Apachne reverse proxy. Here is a sample directive for running this URL
shortener behind an Apache reverse proxy. It will enable the proxy to run under
the `/u/` path, assuming PORT is set to 8880.


	# Rewrite /u/ for url shortener
	ProxyPass /u/ http://localhost:8880/
	ProxyPassReverse /u/ http://localhost:8880/

We assume that this shortener is for personal use only, and that the
BaseHTTPServer.BaseHTTPRequestHandler is single-threaded, so we worry about
neither data races nor high throughput.

The initial implementation stores all data in memory, so redirects only persist
as long as the process is not killed.

## References.

 - [https://github.com/python/cpython/blob/2.7/Lib/BaseHTTPServer.py]
 - [https://stackoverflow.com/a/3389505]
 - [https://docs.python.org/2/howto/logging.html]
