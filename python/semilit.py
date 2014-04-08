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

- code as flat-pages
--------------------
The code files are published directly to the web. Some meta data is attached to the header to categorize
them and provide additional information such as status, date, tags etc. For every project there is just
one file, which is also the working code. The overhead couldn't be less.

For every language there is separate folder. For now, there is a `python` and a `javascript` folder, but
who knows I will get to do `haskell` one day.

- github pages
--------------
Proper source control management is keeping me sane and Github is doing a nice job hosting
[this repository](https://github.com/snirp/infinite-student). The thing that sets Github apart is the
ability to host static files, so I can use one environment for version control and hosting.

- semiliterate programming
---------------------------
Semiliterate programming can be seen as the common ground between "literate programming" and the more
conventional appoaches.

> Literate programming is an approach to programming introduced by Donald Knuth in which a program is
given as an explanation of the program logic in a natural language, such as English, interspersed with
snippets of macros and traditional source code, from which a compilable source code can be generated.

This project and the other projects on infinite student deviate from literate programming in the sense
that natural language is not leading. While I fancy the idea, it does not work too well with the
convetional programming skills I am trying to attain. The projects are rather conventional files
interspersed with extensive documentation and elaboration with additional formatting. For this purpose,
special multiline comment blocks are used, which are marked by `<` and `>`.

When the interpreter reads the file, these blocks for meta-data and documentation are treated as any
other comment. When the web application parses the code files, the documentation is rendered as Markdown
and the code as Markdown code blocks with highlighting. The first documentation block is parsed as YAML
meta-data about the project.


Flask and static sites
======================
This sets the bar for our web application. It should:

+ Deal with multiple folders with code files, one for every language;
+ Parse the code files into a metadate and a formatted webpage;
+ Use the meta-data to make the pages accessible.
+ Provide the additional pages and templates, such as the landing page.

The Flask webframework is the perfect Python solution to doing this within the bounds of a single file.
It can be used to serve the pages dynamically (with caching), or statically after 'freezing' them with
Frozen Flask.

This amounts to building a custom 'static site generator'. Many projects exist that attempt to do the
same, but these lack the flexibilty needed to adapt to my use case. Using Flask gives me much more power
and flexibilty. Moreover, building a static site generator is pretty trivial if you use Frozen Flask.

>"""

import io
import os
import yaml
import markdown as markdown_module
import datetime
import re
import werkzeug
import pygments.formatters
from flask import Flask, Markup, render_template, abort, render_template_string, url_for
from flask_frozen import Freezer

### initialization ###
app = Flask(__name__)

### configuration ###
PYGMENTS_CSS = (pygments.formatters.HtmlFormatter(style='trac')
                .get_style_defs('.codehilite'))

app.config['FREEZER_DESTINATION'] = 'gh-pages'
app.config['FREEZER_DESTINATION_IGNORE'] = ['.git*', 'CNAME', '.gitignore', 'readme.md']
app.config['FREEZER_RELATIVE_URLS'] = True
app.config['FREEZER_BASE_URL'] = 'TODO'  # TODO freezer uses this for _external=True URLs

freezer = Freezer(app)


@app.template_filter()
def markdown(text, extensions=['codehilite(linenums=False)', 'fenced_code', 'tables'] + 2 * ['downheader']):
    """render markdown to HTML, possibly using custom extensions"""
    return markdown_module.markdown(text, extensions)

"""<
Put it in the freezer
=====================
As we said, this is a normal Flask application and can be run and tested as such. By calling
`freezer.freeze()`, the application will be frozen into the FREEZER_DESTINATION folder as a
collection of static files.

By creating a separate `gh-pages` branch in the git repository to track the static folder, github
will serve the folder as a static website.


Deal with code files
=====================
For every programming language I am making projects in, there is an instance of the Pages class.
For example: `python = Pages(flatdir='python', language='python', suffix='.py')`.

The heavy work is done in the `get_page()` method. It parses the file in the fashion of a lexer
to obtain the DOC and CODE sections or 'tokens'. The first DOC section forms the (YAML) head. The
various other sections are processed (indentations, fenced code block) and reassembled as the
(Markdown) body of the flatpage.

Some language implementations dictate that the first line of a code file contains a 'shebang' or
an encoding declaration (`#!` or `#`). To avoid having these before the first DOC block in the output,
they are isolated and prepended before the first CODE block.

The lexer works by matching regular expressions against the code file. This is generally not recommended,
because programming languages are not 'regular' and of higher complexity. It can lead to undesireable
results, but because this is a controlled environment I decided to go ahead with it.

>"""


### flatpage classes ###
class Pages(object):
    """
    Several distinct Pages . Caching is implemented for the properties and HTML content of the pages.

    Attributes:
        _cache          Stores Page-instance and last-modified per flatpage filepath.
        _languagemap    Provides suffix and multiline comment patterns per language.

    Arguments (instance specific):
        flatdir         Directory that holds the code files.
        flatroot        Full path to the fladir directory
        language        Name of the language.
        suffix          Only files with matching suffix will be rendered.
        start_pattern,
        end_pattern     Everything inside these patterns will be treated as Markdown;
                        the sections in between as (Markdown) code blocks.
        chars           Number of characters of the patterns, used for some messy slicing.
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


"""<
Caching
=======
For every call to the `get_page()` method, the Page class is instantiated: a Page
object exists for every code file. It is stored in a cache, together with the datestamp
of the file. If `get_page()` is called again, a check is performed to see whether the
file is still current. If the file is edited, the object in cache is replaced by creating
a new instance of Page for the file.

The caching is only relevant if the application is run dynamically: it is not relevant for
the frozen/static website.

Rendering
=========
The `html()` method does the heavy work of rendering the Markdown code to HTML. First we
render any Jinja template tags so we can include images and such. Next the Markdown is
rendered with several extensions:

+ codehilite: Syntax highlighting
+ fenced_code: Indicate code blocks by triple backticks (```)
+ tables: Simple Markdown tables
+ 2 * downheader: Start with a lower HTML header tag (H3) inside the pages.

>"""

class Page(object):
    """
    Renders body to HTML and parse head to meta properties.

    Arguments (instance specific):
        name            Derived from filename of the flatfile.
        head            String to be rendered as YAML to properties
        body            String to be rendered as Markdown to HTML
        flatdir         Used to match Page object to its url's
        github_link     Location of the underlying file on Github
    """

    def __init__(self, name, head, body, flatdir):
        self.name = name
        self.head = head
        self.body = body
        self.flatdir = flatdir
        self.github_link = "https://github.com/%s/%s/blob/master/%s/%s.py" %\
            ('snirp', 'infinite-student', flatdir, name)

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


### instantiate language class ###
python = Pages(flatdir='python', language='python')
javascript = Pages(flatdir='javascript', language='javascript')

"""<
Languages
=========
Here we instantiate python and javascript as project languages. By setting the `language` argument,
the Pages class can get the relevant settings for the language from the `_languagemap` (see Pages
class). It tells us that python files have a ".py" suffix and that the multiline comments are defined
by triple quotes.

Views
=====
We can now use regular Flask view functions to generate pages for home, overview, detail and feeds.
None of this should be new if you ever used Flask before; apart from setting an explicit route to
`/404.html`. This is needed to make sure that Frozen Flask will generate a page by that name, just
as Github Pages expects if it cannot resolve a URL.
>"""


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

Further improvements
====================

+ The view functions do not scale very well if the number of languages increases. I should
consider a more generic approach.
+ The parsing under `get_page()` is too deeply nested and complex and thereby incomprehensible.
Consider splitting into a separate method.
+ The regular expression is a bit messy: it leaves superfluous characters. Making this more
elegant would eliminate the need of extra trimming.
>"""