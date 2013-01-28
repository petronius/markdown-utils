# Markdown HTTP Server

This is a one-file HTTP server script that acts as a very simple (and slightly stupid) file server. It will automatically convert markdown files to HTML, and serve them as such.

## Usage

    $ python mdserver.py [document root] [port number]

If the document root is not specified, the current working directory will be used. The default port is 8080.

## Todo

* Add Etag and 302 Not Modified support
* Custom error files
* Automatic CSS style inclusion (see mdbuild in this project)

## Requirements

Requires the Python [Markdown module](http://pypi.python.org/pypi/Markdown).

This should work in all versions of Python 2.5+, and in Python 3 with some slight tweaking of the imports (the SimpleHTTPServer class has moved to the html.server module in Python 3).
