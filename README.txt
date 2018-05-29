## Minimal URL Shortener

This URL shortener is designed to run either on its own web server or behind an
Apachne reverse proxy. Here is a sample directive for running this URL
shortener behind an Apache reverse proxy. It will enable the proxy to run under
the `/u/` directory, assuming the PORT is set to 8880.


	# Rewrite /u/ for url shortener
	ProxyPass /u/ http://localhost:8880/
	ProxyPassReverse /u/ http://localhost:8880/


The initial implementation stores all everything in memory, so redirects only
persist as long as the process is not killed.

