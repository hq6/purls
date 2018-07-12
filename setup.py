from setuptools import setup

long_description=\
"""
purls.py
==================
Personal URL Shortener.

Today, we can use bit.ly or goo.gl or any of the other publicly available URL
shorteners out there, but doing so limits us in the shortURLs we can choose,
because the namespace is crowded with every other user.

With the abundance of new TLDs, it is once again possible for an individual to
register a short personal domain relatively cheaply.  With that domain in hand,
purls.py allows one to quickly and easily host one's own URL shortener with
minimal dependencies and almost no setup.

Usage
==================

purls.py runs on port 8880 by default, so if one is running Apache primarily,
the following two lines of configuration in the Apache configuration file are
sufficient to redirect the prefix /r/ to purls.py::

    ProxyPass /u/ http://localhost:8880/
    ProxyPassReverse /u/ http://localhost:8880/


The simplest invocation of purls.py requires only the domain prefix of the
shortened URL's to be passed. For example, if my domain prefix is
https://hq6.me/r/, I can invoke purls as follows::

    python purls.py https://hq6.me/r/

"""

setup(
  name="purls",
  version='0.0.1',
  scripts=['purls.py'],
  install_requires=['docopt>=0.2'],
  author="Henry Qin",
  author_email="root@hq6.me",
  description="Personal URL shortener for personal domains.",
  long_description=long_description,
  platforms=["Any Platform supporting ANSI escape codes"],
  license="MIT",
  url="https://github.com/hq6/purls"
)
