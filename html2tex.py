# pylint: disable=missing-docstring, too-many-ancestors
from urllib.error import HTTPError
from urllib.request import urlretrieve
from pathlib import Path

from bs4 import BeautifulSoup as Bs

from pylatex import Document, Section, Subsection, Figure, SubFigure
from pylatex.base_classes import (
        Environment, Arguments, ContainerCommand, Command)
from pylatex.package import Package
from pylatex.utils import NoEscape, bold, escape_latex

# tag handlers index
TAGS = {
}

MEDIA='media'

DEBUG = True

LST_COMMANDS = NoEscape(
    "\\lstset{%\n"
    "\tbackgroundcolor=\\color{white},\n"
    "\tbasicstyle=\\footnotesize,\n"
    "\tbreakatwhitespace=false,\n"
    "\tbreaklines=true,\n"
    "}\n"
)

PG_COMMANDS = NoEscape(
    "\\setmainlanguage{russian}\n"
    "\\setotherlanguage{english}\n"
    "\\setkeys{russian}{babelshorthands=true}\n\n"
    "\\setmainfont{Times New Roman}\n"
    "\\setromanfont{Times New Roman}\n"
    "\\setsansfont{Arial}\n"
    "\\setmonofont{Source Code Pro}\n\n"
    "\\newfontfamily{\\cyrillicfont}{Times New Roman}\n"
    "\\newfontfamily{\\cyrillicfontrm}{Times New Roman}\n"
    "\\newfontfamily{\\cyrillicfonttt}{Source Code Pro}\n"
    "\\newfontfamily{\\cyrillicfontsf}{Arial}\n"
)

class Lstlisting(Environment):
    escape = False
    content_separator = '\n'

class Footnote(ContainerCommand):
    _latex_name = "footnote"

class HabrBook(Document):
    packages = [
        Package('xltxtra'),
        Package('polyglossia'),
        Package('color'),
        Package('listings'),
        Package('hyperref')
    ]

    def __init__(self):
        super().__init__(fontenc="T2A")
        self.preamble.append(PG_COMMANDS)
        self.preamble.append("")
        self.preamble.append(LST_COMMANDS)

def tag_handler(name):
    def handle(func):
        TAGS[name] = func
        def decorate(*args, **kwargs):
            return func(*args, **kwargs)
        return decorate
    return handle

def process_tag(parent, tag):
    if tag.name is None:
        if tag.string.strip():
            process_string(parent, tag.string)
        return
    handler = TAGS.get(tag.name)
    if handler:
        handler(parent, tag)
    else:
        print('unknown tag:', tag.name)
        print(tag)


def download_image(image_url):
    media = Path(MEDIA)
    if not(media.exists()):
        media.mkdir()

    imgfile = image_url.split('/')[-1]
    if not (media/imgfile).exists():
        try:
            urlretrieve(image_url, str(media/imgfile))
        except HTTPError:
            print('cannot download', image_url)
            return None
    return media/imgfile


def process_string(parent, navstr):
    parent.append(navstr)

@tag_handler('h1')
def h1(doc, tag):
    doc.preamble.append(Command('title', tag.text.strip()))
    doc.append(NoEscape('\\maketitle\n'))

@tag_handler('h2')
def h2(doc, tag):
    doc.append(Section(tag.text.strip()))

@tag_handler('h3')
def h3(doc, tag):
    doc.append(Subsection(tag.text.strip()))

@tag_handler('p')
def par(parent, tag):
    par = []
    processed_par = []
    parent.append(Command('par'))
    for child in tag:
        process_tag(par, child)
    for child in par:
        if hasattr(child, 'dumps'):
            processed_par.append(child.dumps())
        else:
            processed_par.append(child)
    parent.append(NoEscape(''.join(processed_par)))


@tag_handler('pre')
def pre(parent, tag):
    with parent.create(Lstlisting()):
        for child in tag:
            process_tag(parent, child)

@tag_handler('code')
def code(parent, tag):
    if tag.parent.name == 'pre':
        for child in tag:
            process_tag(parent, child)
    else:
        text = tag.string
        parent.append(f"{{\\footnotesize\\texttt{{{escape_latex(text)}}}}}")

@tag_handler('div')
def div(parent, tag):
    for child in tag:
        process_tag(parent, child)

@tag_handler('strong')
def strong(parent, tag):
    parent.append(bold(tag.text.strip()))

@tag_handler('a')
def href(parent, tag):
    parent.append(NoEscape(r"\\"))
    parent.append(Command('href', arguments=Arguments(tag.text, tag['href'])))

@tag_handler('img')
def img(parent, tag):
    imgpath = str(download_image(tag['src']))
    if imgpath is None:
        return
    figure = Figure()
    figure.add_image(imgpath, width=NoEscape(r'\linewidth'))
    parent.append(figure)

@tag_handler('em')
def footnote(parent, tag):
    newsoup = Bs('', 'lxml')
    for child in tag:
        if child.name is None:
            newtag = newsoup.new_tag(name='code')
            newsoup.append(newtag)
            newtag.append(child)
            child = newtag
            print(child)
        process_tag(parent, child)


def process_html(doc, htmlfile):
    h2counter = 0
    with open(htmlfile) as html:
        soup = Bs(html, 'lxml')
    body = soup.html.body
    for tag in body:
        if tag.name is not None:
            if tag.name == 'h2':
                h2counter += 1
            if DEBUG and h2counter > 2:
                return
            process_tag(doc, tag)
        elif tag.string.strip():
            print('debug:', tag.string.strip())

def main():
    doc = HabrBook()
    process_html(doc, 'flask.html')
    doc.generate_tex('test')
    with open('test.tex', 'r+') as texfile:
        text = '% TEX program = xelatex\n' + texfile.read()
        texfile.seek(0)
        texfile.write(text)


if __name__ == '__main__':
    main()
