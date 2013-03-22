#!/usr/bin/env python
"""
A lightweight, simple HTTP file server that automatically converts markdown to
HTML. This *should* work on Python 2.5+, and on Python 3 with a few tweaks of
the imports.
"""

# TODO:
#
# * E-Tags and 302 not modifieds
# * Error files
# * Default styles
#
#

import os
import sys
import cgi
import urllib
import urlparse
import posixpath

import StringIO

import SimpleHTTPServer
import BaseHTTPServer
import SocketServer
import markdown

md = markdown.Markdown()

__all__ = ['MDServer', 'MDHandler']

def format_title(t):
    return os.path.basename(t).split('.')[0].replace('_', ' ').title()


class HTMLDoc(object):

    template = """%(doctype)s
<html>
<head>
%(head)s
</head>
<body>
%(body)s
</body>
</html>"""

    def __init__(self, title, doctype='<!doctype html>'):
        self.title = title
        self.doctype = doctype
        self.head_lines = []
        self.body_lines = []
        self.head_line('<title>%s</title>' % title)

    def head_line(self, line):
        self.head_lines.append(line)

    def body_line(self, line):
        self.body_lines.append(line)

    def render(self):
        out = self.template % {
            'doctype': self.doctype,
            'title': self.title,
            'head': '\n'.join(self.head_lines),
            'body': '\n'.join(self.body_lines),
        }
        return out


class MDServer(BaseHTTPServer.HTTPServer, SocketServer.ThreadingMixIn):

    def __init__(self, server_address, RequestHandlerClass,
                 working_directory = None,
                 error_directory = None,
                 list_empty_dirs = True,
                 default_title = 'Untitled',
                 hide_dotfiles = False,
                 site_name = None):

        self.server_address = server_address
        self.RequestHandlerClass = RequestHandlerClass
        self.RequestHandlerClass.server = self
        self.handler_working_directory = working_directory
        self.handler_list_empty_dirs = list_empty_dirs
        self.handler_error_directory = error_directory
        self.handler_hide_dotfiles = hide_dotfiles
        self.default_title = default_title
        self.site_name = site_name or os.path.basename(os.getcwd()).title()

        try:
            super(MDServer, self).__init__(self, server_address, RequestHandlerClass)
        except:
            BaseHTTPServer.HTTPServer.__init__(self, server_address, RequestHandlerClass)
        

class MDHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):    

    def __init__(self, *args, **kwargs):
        
        if self.server.handler_working_directory:
            self.working_directory = self.server.handler_working_directory
        else:
            self.working_directory = os.getcwd()

        if self.server.handler_error_directory:
            self.error_directory = self.server.handler_error_directory
        else:
            self.error_directory = self.working_directory + '/.errors/'

        self.list_empty_dirs = self.server.handler_list_empty_dirs
        self.site_name = format_title(server.site_name)
        self.default_title = server.default_title

        try:
            super(MDHandler, self).__init__(*args, **kwargs)
        except:
            SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(self, *args, **kwargs)
        

    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        ---

        / -> /index.md
        /somedir.html -> /somedir.md
        /somedir/ -> /somedir.md
        /somedir/ -> /somedir/index.md

        """
        # abandon query parameters
        possible_paths = []
        path = urlparse.urlparse(path)[2]
        path = posixpath.normpath(urllib.unquote(path))
        possible_paths.append(path)
        if not '.' in os.path.basename(path)[1:]:
            for ex in ['.md', '/index.md']:
                possible_paths.append(path + ex)
        for path in possible_paths:
            words = path.split('/')
            words = filter(None, words)
            path = self.working_directory
            for word in words:
                drive, word = os.path.splitdrive(word)
                head, word = os.path.split(word)
                if word in (os.curdir, os.pardir):
                    continue
                if word.startswith('.'):
                    return self.not_found() # disallow dot directories
                path = os.path.join(path, word)
            if os.path.exists(path):
                return path
        else:
            
            return self.not_found()
        
        
    def error_file(self, errno):
        """
        
        """
        path = self.error_directory + '/' + str(errno) + '.md'
        if os.path.exists(path):
            return path
        else:
            return self.error_directory + '/default.md'


    def not_found(self):
        """
        404
        """
        self.send_response(404)
        self.end_headers()
        return self.error_file(404)


    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """
        path = self.translate_path(self.path)
        if not path:
            return
        f = None
        ctype = None
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return None
            else:
                return self.list_directory(path)
        if path.endswith('.md'):
            ctype = 'text/html' # This will be the result
        if not ctype:
            ctype = self.guess_type(path)
        if ctype.startswith('text/'):
            mode = 'r'
        else:
            mode = 'rb'
        try:
            f = open(path, mode)
        except (IOError,):
            e = sys.exc_info()[1]
            self.send_error(404, "File not found")
            return None
        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f
    

    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).

        Return value is either a file object, or None (indicating an
        error).  In either case, the headers are sent, making the
        interface the same as for send_head().

        """
        if self.list_empty_dirs:
            try:
                list = os.listdir(path)
            except (os.error,):
                e = sys.exc_info()[1]
                self.send_error(404, "No permission to list directory")
                return None
            list.sort(key=lambda a: a.lower())
            f = StringIO.StringIO()
            displaypath = cgi.escape(urllib.unquote(self.path))

            dir_title = ' | '.join(filter(None, [self.site_name, "Directory listing for %s" % displaypath]))
            html = HTMLDoc(dir_title)
            html.body_line("<h1>Directory listing for %s</h1>" % displaypath)
            html.body_line("<hr>\n<ul>")
            if self.path != '/':
                html.body_line('<li><a href="..">..</a></li>')
            for name in list:
                if self.server.handler_hide_dotfiles and name.startswith('.'):
                    continue
                fullname = os.path.join(path, name)
                displayname = linkname = name
                # Append / for directories or @ for symbolic links
                if os.path.isdir(fullname):
                    displayname = name + "/"
                    linkname = name + "/"
                if os.path.islink(fullname):
                    displayname = name + "@"
                    # Note: a link to a directory displays with @ and links with /
                html.body_line('<li><a href="%s">%s</a></li>'
                        % (urllib.quote(linkname), cgi.escape(displayname)))
            html.body_line("</ul>\n<hr>")
            f.write(html.render())
            length = f.tell()
            f.seek(0)
            self.send_response(200)
            encoding = sys.getfilesystemencoding()
            self.send_header("Content-type", "text/html; charset=%s" % encoding)
            self.send_header("Content-Length", str(length))
            self.end_headers()
            return f


    def do_GET(self):
        f = self.send_head()
        title = None
        if f:
            if hasattr(f, 'name') and f.name.endswith('.md'):
                title = format_title(f.name)
                title_parts = []
                if self.site_name:
                    title_parts.append(self.site_name)
                if title or self.default_title:
                    title_parts.append(title or self.default_title)
                doc = HTMLDoc(' | '.join(title_parts))
                f.seek(0)
                html = md.convert(f.read().encode('utf8'))
                doc.body_line(html)
                f.close()
                f = StringIO.StringIO()
                f.write(doc.render())
                f.seek(0)
            self.copyfile(f, self.wfile)
            f.close()


if __name__ == "__main__":

    def out(msg): # compatibility function
        sys.stderr.write('\n' + msg)

    usage = """
    Usage: %s [document root]

    If the document root is not specified, the current working directory will be
    used.
    """ % os.path.basename(sys.argv[0])

    host = ''
    try:
        port = int(sys.argv[1])
    except (ValueError,IndexError,):
        out('A valid port was not specified. Trying to use port 8080 ...\n')
        port = 8080

    working_dir = None
    for arg in sys.argv[1:]:
        if arg in ['-h', '--help']:
            import textwrap
            out(textwrap.dedent(usage))
            exit()
        else:
            working_dir = arg

    server_address = ("", port)
    server = MDServer(server_address, MDHandler, working_directory = working_dir, list_empty_dirs = True, hide_dotfiles = True)
    server.serve_forever()
