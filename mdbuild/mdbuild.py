#!/usr/bin/env python
"""
python mdbuild.py <source dir> <target dir> [--config=file] [--dev|--live|--clean]

Build a directory of Markdown files into a static HTML directory tree. If no
config file is specified, the script will look for a 'config.py' in the source
directory.

All non-markdown files not in the source tree and not matching one of the
'ignore' expressions are copied directly to the destination tree.

This should be compatible with Python 2 and 3.

---

# example config.py

styles = {     # A list of stylesheet URLs to include
    'live': [] # Styles that are always included
    'dev': []  # Styles that are not included in live builds
}

scripts = {     # A list of script URLs to include
    'live': []  # Scripts that are always included
    'dev': []   # Scripts that are not included in live builds
}

ignore = [
    r'\.py(c)?$',
]


"""

import re
import os
import sys
import imp
import bs4
import shutil
import markdown

md = markdown.Markdown()


def out(*args):
    """
    Version agnostic printing.
    """
    msg = ' '.join(args)
    sys.stdout.write(msg+'\n')


def fpjoin(*args):
    args = list(args)
    for k,arg in enumerate(args):
        args[k] = arg.strip(os.path.sep)
    return os.path.sep.join(args)


def matches_found(text, regex_list):
    for pattern in regex_list:
        if re.match(pattern, text):
            out('Skipping', text, '- matches', pattern)
            return True


def run(source, target, dev, conf = None):
    """
    Main script body. Load the config file and walk the 'source' directory tree.
    """

    if not conf:
        conf = fpjoin(source, 'config.py')

    config = {}
    if conf:
        c = imp.load_source('config_file', conf)
        for key in dir(c):
            config[key] = getattr(c, key)

    styles = config.get('styles', {}).get('live', [])
    if dev:
        styles += config.get('styles', {}).get('dev', [])

    scripts = config.get('scripts', {}).get('live', [])
    if dev:
        scripts += config.get('scripts', {}).get('dev', [])

    ignore = config.get('ignore', [])

    for root, _, files in os.walk(source):
        path = fpjoin(target, root)
        if not os.path.exists(path):
            os.makedirs(path)
        for file in files:
            if matches_found(file, ignore):
                continue
            if file.endswith('.md'):
                doctitle = ' '.join(file.split('.')[0].split('_')).title()
                inpath = fpjoin(root, file)
                filename = file[:-3]
                filename += '.html'
                filepath = fpjoin(path, filename)
                inf = open(inpath, 'r')
                data = inf.read()
                inf.close()
                data = md.convert(data)
                soup = bs4.BeautifulSoup(data, "html5lib")
                titletag = soup.new_tag('title')
                titletag.append(doctitle)
                soup.html.head.append(titletag)
                for url in styles:
                    newtag = soup.new_tag("link", rel = 'stylesheet', href = url, type = 'text/css')
                    soup.html.head.append(newtag)
                for url in scripts:
                    newtag = soup.new_tag('script', src = url, type='text/javascript')
                    soup.html.head.append(newtag)
                output = soup.prettify(formatter = 'html')
                # Fix link output (don't add extra spaces at the end of link
                # tags - this messes up text layout)
                output = re.sub(r'([a-zA-Z0-9])(\s+)\<\/a\>\s*(\.)?',
                                r'\1</a>\3', output)
                otf = open(filepath, 'w')
                otf.write('<!doctype html>\n')
                otf.write(output)
                otf.close()
                out(inpath, '->', filepath)
            else:
                sourcepath = fpjoin(root, file)
                targetpath = fpjoin(path, file)
                shutil.copy2(sourcepath, targetpath)
                out(sourcepath, '->', targetpath)



if __name__ == "__main__":
    
    source_dir = None
    target_dir = None
    conf_file = None
    dev = True
    clean = False

    for arg in sys.argv[1:]:
        if arg.startswith('--'):
            if arg == '--dev':
                dev = True
            elif arg == '--live':
                dev = False
            elif arg == '--clean':
                clean = True
            else:
                conf_file = arg.split('=')[1]
        else:
            if not source_dir:
                source_dir = arg
            else:
                target_dir = arg

    if not (source_dir and target_dir):
        out(__doc__)
        exit(1)
    else:
        if not clean:
            run(source_dir, target_dir, dev, conf_file)
        else:
            for f in os.listdir(target_dir):
                path = fpjoin(target_dir, f)
                out('removing', path)
                try:
                    shutil.rmtree(path)
                except (OSError,): # version agnostic exception handling
                    e = sys.exc_info()[1]
                    if e.errno == 20:
                        # path is a file
                        os.remove(path)