# Markdown source builder

This simple script will compile a directory tree of files into an identical tree, but with all markdown files converted to pretty-printed HTML. The configuration file allows you to specify additional style or script files to be added to the HTML header. All non-markdown files in the source tree are copied directly, allowing you to store CSS and Javascript with the markdown source.

By default, the title of each HTML document will always be the document's filename, converted from *snake_case* to *Title Case*. To override this scheme, you can tag a file with a new document title using the following syntax on the first line of the file:
  
    # TITLE: <page title>

## Options and arguments

This script can be made executable, or invoked through python. Either way, the arguments are the same:

    $ python mdbuild.py <source dir> <target dir> [--config=file] [--dev|--live|--clean]

If the `--config` option is not specified, it is assumed that there is a config.py file residing in the root of `&lt;source dir&gt;`.

The `--dev` flag is understood to be on by default, unless `--live` is present. The only difference is which script/style URLs are included (see 'Configuration', below).

The `--clean` option will delete all files and directories in the `&lt;target dir&gt;` directory.

## Configuration

The configuration file is a standard Python file, with three possible entries:

    styles = {     # A list of stylesheet URLs to include
        'live': [] # Styles that are always included
        'dev': []  # Styles that are not included in live builds
    }
    
    scripts = {     # A list of script URLs to include
        'live': []  # Scripts that are always included
        'dev': []   # Scripts that are not included in live builds
    }
    
    # Files matching entries in this list will be ignored altogether
    ignore = [
        r'\.py(c)?$',
    ]

## Requirements

This script makes use of [BeautifulSoup4](http://www.crummy.com/software/BeautifulSoup/bs4/) and the Python [Markdown module](http://pypi.python.org/pypi/Markdown).
