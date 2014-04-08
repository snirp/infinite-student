"""<
# This code file follows the SLiP (Semi-Literate Programming) annotation convention.
# specification at: ...
title:      "Static site generator for SLiP (Semi-Literate Programming) files"
author:     Roy Prins
published:  17-04-2014
status:     project
completed:  100
summary: >
    A Flask based Static Site Generator that powers the Infinite Student website.
>"""

"""<
The goal
========
This is the project that powers the Infinite Student website. I set myself the following goals:

+ Minimal overhead in making new projects or listing ideas;
+ Extendable to multiple languages;
+ Easy hosting and git-based workflow;
+ Force myself to do extensive documentation.

Meanwhile I am well aware that this will not fit all the projects I have in mind. The idea is to
use it to envision, publish and keep developing simple single-file projects. By myself or even
with a collaborator. Anything with a bigger scope will find a home outside the Infinite Student project.

Here is what I came up with:

Code as flat-pages
------------------
The code files are published directly to the web. Some meta data is attached to the header to categorize
them and provide additional information such as status, date, tags etc. For every project there is just
one file, which is also the working code. The overhead couldn't be less.

For every language there is separate folder. For now, there is a `python` and a `javascript` folder, but
who knows I will get to do `haskell` one day.

Github pages
------------
Proper source control management is keeping me sane and Github is doing a nice job hosting
[this repository](https://github.com/snirp/infinite-student). The thing that sets Github apart is the
ability to host static files, so I can use one environment for version control and hosting.

Semi-literate programming
-------------------------




Flask and static sites
======================



>"""

import io
import os
import yaml
import markdown as markdown_module
import datetime
import re
import itertools
import werkzeug
import pygments.formatters
from flask import Flask, Markup, render_template, abort, render_template_string, url_for

### initialization ###
app = Flask(__name__)

### configuration ###
app.config['FREEZER_DESTINATION'] = 'gh-pages'
app.config['FREEZER_DESTINATION_IGNORE'] = ['.git*', 'CNAME', '.gitignore', 'readme.md']
app.config['FREEZER_RELATIVE_URLS'] = True
app.config['FREEZER_BASE_URL'] = 'TODO'  # TODO freezer uses this for _external=True URLs

PYGMENTS_CSS = (pygments.formatters.HtmlFormatter(style='trac')
                .get_style_defs('.codehilite'))


@app.template_filter()
def date(value):
    return value.strftime('%e %b %Y')

@app.template_filter()
def markdown(text, extensions=['codehilite(linenums=False)', 'fenced_code', 'tables'] + 2 * ['downheader']):
    """render markdown to HTML, possibly using custom extensions"""
    return markdown_module.markdown(text, extensions)

"""<
Static site generator
=====================

>"""


### flatpage classes ###
class Pages(object):
    """
    Several distinct Pages . Caching is implemented for the properties and HTML content of the pages.

    Attributes:
        _cache          Stores Page-instance and last-modified per flatpage filepath.
        _languagemap    Provides suffix and multiline comment patterns per language.

    Arguments (instance specific):
        flatdir         Directory that holds the flat markup files.
        flatroot        Full path to the fladir directory
        suffix          Only files with matching suffix will be rendered.
        start_pattern,
        end_pattern     Everything inside these patterns will be treated as Markdown;
                        the sections in between as (Markdown) code blocks.
    """
    _cache = {}
    _languagemap = {
        'python': {'suffix': '.py', 'docstart': '\"{3}<', 'docend': '>\"{3}', 'chars': 4},
        'javascript': {'suffix': '.js', 'docstart': '/\*<', 'docend': '>\*/', 'chars': 3},
        'java': {'suffix': '.java', 'docstart': '/\*<', 'docend': '>\*/', 'chars': 3},
        'haskell': {'suffix': '.hs', 'docstart': '{-<', 'docend': '>-}', 'chars': 3}
    }

    def __init__(self, flatdir='pages', language='python', suffix=''):
        self.flatdir = flatdir
        self.flatroot = os.path.join(app.root_path, flatdir)
        self.language = language
        if suffix:
            self.suffix = suffix
        else:
            self.suffix = self._languagemap[language]['suffix']
        self.start_pattern = self._languagemap[language]['docstart']
        self.end_pattern = self._languagemap[language]['docend']
        self.chars = self._languagemap[language]['chars']

    def all_pages(self):
        """Generator that yiels a Page instance for every flatfile"""
        if not os.path.isdir(self.flatroot):
            abort(404)
        for filename in os.listdir(self.flatroot):
            if filename.endswith(self.suffix):
                yield self.get_page(filename[:-len(self.suffix)])

    def draft_pages(self):
        """return only draft pages"""
        return [p for p in self.all_pages() if p['status'] == 'draft']

    def published_pages(self):
        """return project pages, sorted by published date"""
        return sorted([p for p in self.all_pages() if p['status'] == 'project'],
                      reverse=True, key=lambda p: p['published'])

    def lastmod_pages(self):
        """sorts published pages by lastmod property"""
        return sorted(self.published_pages(), key=lambda p: p.lastmod())

    def tagged_pages(self, tag):
        return [p for p in self.published_pages() if tag in p['tags']]

    def get_page(self, name):
        """
        Return a Page instance from cache or instantiate a new one if outdated or absent.
        The file content is split in a (Markdown) body and (YAML) head section.
        Update the cache with the new or updated Page instance.
        """
        filepath = os.path.join(self.flatroot, name+self.suffix)
        if not os.path.isfile(filepath):
            abort(404)
        mtime = os.path.getmtime(filepath)
        page, old_mtime = self._cache.get(filepath, (None, None))
        if not page or mtime != old_mtime:
            with io.open(filepath, encoding='utf8') as fd:
                filecontent = fd.read().splitlines()
            #capture encoding header: find the first line not starting with '#'
            i = 0
            for line in filecontent:
                if not line.startswith('#'):
                    break
                i += 1
            encoding_section = '\n'.join(filecontent[:i])
            content_section = '\n'.join(filecontent[i:])

            #lexer rules
            doc_pattern = '(?=%s)(.*?)(?=%s)' %(self.start_pattern, self.end_pattern)
            code_pattern = '(?=%s)(.+?)(?=%s)' %(self.end_pattern, self.start_pattern)
            rules = (("DOC", doc_pattern), ("CODE", code_pattern),)
            regexp = re.compile("|".join(["(?P<%s>%s)" % (n, p) for n, p in rules]), re.M | re.DOTALL | re.U)

            head = ''
            body = ''
            first_codeblock = True
            first_docblock = True
            for match in regexp.finditer(content_section):
                for group, pattern in rules:
                    tok = match.group(group)
                    if tok is not None:
                        #trim doc divider
                        tok = tok[self.chars:]
                        #capture head block (YAML)
                        if group == 'DOC' and first_docblock:
                            first_docblock = False
                            head = tok
                            break
                        #skip empty code blocks
                        elif group == 'CODE' and tok.isspace():
                            break
                        #prepend the encoding header to the first code block
                        elif group == 'CODE' and first_codeblock:
                            first_codeblock = False
                            tok = encoding_section + tok
                        #unindent the documentation sections
                        if group == "DOC":
                            tok = "\n".join(i.lstrip() for i in tok.splitlines())
                        #create fenced code blocks with language declaration
                        elif group == "CODE":
                            tok = "\n\n```\n:::%s\n%s\n```\n" % (self.language, tok)
                        body += tok
            page = Page(name, head, body, self.flatdir)
            self._cache[filepath] = (page, mtime)
        return page

    def load_tags(self):
        tags = []
        for page in self.all_pages():
            tags = page['tags'] + tags
        return sorted(set(tags))


class Page(object):
    """
    Renders body to HTML and parse head to meta properties.

    Arguments (instance specific):
        name            Derived from filename of the flatfile.
        head            String to be rendered as YAML to properties
        body            String to be rendered as Markdown to HTML
        flatdir         Used to match Page object to its url's
    """

    def __init__(self, name, head, body, flatdir):
        self.name = name
        self.head = head
        self.body = body
        self.flatdir = flatdir
        self.github_link = "https://github.com/%s/%s/blob/master/%s/%s.py" %\
            ('snirp', 'eternal-student', flatdir, name)

    def __getitem__(self, name):
        """getter to access the meta properties directly"""
        return self.meta.get(name)

    @werkzeug.cached_property
    def meta(self):
        """Render head section of file to meta properties."""
        return yaml.safe_load(self.head) or {}

    @werkzeug.cached_property
    def html(self):
        """Render Markdown and Jinja tags to HTML."""
        html = render_template_string(Markup(self.body))
        html = markdown_module.markdown(html, ['codehilite(linenums=False)', 'fenced_code', 'tables'] + 2*['downheader'])
        return html

    def lastmod(self):
        return self.meta.get('updated', self['published'])

    def url(self, **kwargs):
        """Return the url function for the detail page, based on convention of:
        <flatfile directory>_detail"""
        return url_for(self.flatdir+'_detail', name=self.name, **kwargs)


### instantiate flatpage class ###
python = Pages('python', 'python')
javascript = Pages('javascript', 'javascript')

### views ###
@app.route('/')
def home():
    return render_template('index.html', pageid='page-home')

@app.route('/python.html')
def python_index():
    projects = python.published_pages()
    return render_template('project-list.html', pageid='page-project', projects=projects)

@app.route('/project/atom.xml')
def project_feed():
    articles = python.lastmod_pages()[:10]
    feed_updated = articles[0].lastmod()
    xml = render_template('atom.xml', articles=articles, feed_updated=feed_updated)
    return app.response_class(xml, mimetype='application/atom+xml')

@app.route('/python/<name>.html')
def python_detail(name):
    p = python.get_page(name)
    return render_template('project-detail.html', pageid='page-python', p=p)

@app.route('/js/<name>.html')
def js_detail(name):
    p = javascript.get_page(name)
    return render_template('project-detail.html', pageid='page-js', p=p)

@app.route('/sitemap.xml')
def generate_sitemap():
    # List of sites with manually added date(time) of last edit.
    sites = [
        (url_for('home', _external=True),       '2014-02-13'),
        (url_for('project_index', _external=True),  '2014-02-13'),
        (url_for('project_feed', _external=True),   '2014-02-15')
    ]
    sites = [(s[0], datetime.date(*[int(ds) for ds in s[1].split('-')])) for s in sites] + \
            [(t.url(_external=True), t.lastmod()) for t in python.published_pages()]
    xml = render_template('sitemap.xml', sites=sites)
    return app.response_class(xml, mimetype='application/atom+xml')


@app.route('/style.css')
def stylesheet():
    css = render_template('style.css', pygments_css=PYGMENTS_CSS)
    return app.response_class(css, mimetype='text/css')

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html', pageid='page-404')

@app.route('/404.html')
def error_freeze():
    """explicitly set a route so that 404.html exists in gh-pages"""
    return render_template('404.html', pageid='page-404')


### launch ###
if __name__ == "__main__":
    app.run(debug=True)

"""<
References
==========

+ [Exyr.org source code, Simon Sapin](https://github.com/SimonSapin/exyr.org)
+ [Literate programming, Donald Knuth](http://www.literateprogramming.com/knuthweb.pdf)
+ [Flask](http://flask.pocoo.org/)
+ [Frozen Flask project](https://pythonhosted.org/Frozen-Flask/)
+ [Github Pages](https://pages.github.com/)
>"""