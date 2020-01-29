# pylint: disable=missing-docstring, too-many-ancestors
import re

from urllib.error import HTTPError
from urllib.request import urlretrieve
from pathlib import Path

from bs4 import BeautifulSoup as Bs

from pylatex import Document, Section, Subsection, Figure, SubFigure, Itemize
from pylatex.base_classes import (
        Environment, Arguments, ContainerCommand, Command)
from pylatex.package import Package
from pylatex.utils import NoEscape, bold, escape_latex

# tag handlers index
TAGS = {
}

MEDIA='media'

DEBUG = True

RUALPHA = re.compile('[А-Яа-я]')


LST_COMMANDS = NoEscape(
    "\\lstset{%\n"
    "\tbackgroundcolor=\\color{white},\n"
    "\tbasicstyle=\\footnotesize,\n"
    "\tbreakatwhitespace=false,\n"
    "\tbreaklines=true,\n"
    "\tinputencoding=utf8,\n"
    "\textendedchars=true,\n"
    "\tescapeinside={\\%*}{*)},\n"
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
    "\\emergencystretch=25pt\n"
)

GLOSSARY = {
        'p': 'par',
        'em': 'emph',
        'blockquote': 'emph'}

class Lstlisting(Environment):
    content_separator = '\n'
    escape = False

class FlatContainer(ContainerCommand):
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._latex_name = name
        self.content_separator = " "

    def __repr__(self):
        return "<FlatContainer>"

    def dumps(self):
        content = self.dumps_content()
        if not content.strip():
            return ''
        result = ''
        start = Command(self.latex_name, arguments=self.arguments, options=self.options)
        result += start.dumps() + '{%\n'
        if content != '':
            result += content + '}\n'
        else:
            result += '}%\n'
        return result


class HabrBook(Document):
    packages = [
        Package('xltxtra'),
        Package('polyglossia'),
        Package('color'),
        Package('listings'),
        Package('hyperref'),
        Package('float'),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

def process_string(parent, tag):
    text = tag.string.strip()
    if not parent._latex_name == 'document' and not check_cyrillic(text):
        parent.append(NoEscape(f"\\begin{{english}}escape_latex({text})\\end{{english}}"))
    else:
        parent.append(text)

def process_tag(parent, tag):
    if tag.name is None:
        if tag.string.strip():
            process_string(parent, tag)
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


@tag_handler('h1')
def h1(doc, tag):
    doc.preamble.append(Command('title', tag.text.strip()))
    doc.append(NoEscape('\\maketitle\n'))

@tag_handler('h2')
def h2(doc, tag):
    doc.append(Section(tag.text.strip()))

@tag_handler('h3')
def h3(doc, tag):
    doc.append(Subsection(tag.text.strip(), label=False))

@tag_handler('em')
@tag_handler('p')
@tag_handler('blockquote')
def line_container(parent, tag):
    latex_name = GLOSSARY.get(tag.name)
    if latex_name is None:
        return
    container = FlatContainer(latex_name)
    for child in tag:
        process_tag(container, child)
    parent.append(container)

@tag_handler('pre')
def pre(parent, tag):
    with parent.create(Lstlisting()):
        for child in tag:
            process_tag(parent, child)

def check_cyrillic(text):
    return bool(RUALPHA.search(text))


@tag_handler('code')
def code(parent, tag):
    if tag.parent.name == 'pre':
        for child in tag:
            process_tag(parent, child)
    else:
        text = tag.string.strip()
        if check_cyrillic(text):
            parent.append(bold(text))
        else:
            #parent.append(NoEscape(f"\\lstinline|{text}|"))
            #parent.append(NoEscape(f"\\begin{{english}}\\texttt{{{escape_latex(text)}}}\\end{{english}}"))
            parent.append(NoEscape(f"\\begin{{english}}\\lstinline|{text}|\\end{{english}}"))

@tag_handler('div')
def div(parent, tag):
    for child in tag:
        process_tag(parent, child)

@tag_handler('strong')
def strong(parent, tag):
    parent.append(bold(tag.text.strip()))

@tag_handler('a')
def href(parent, tag):
    text = tag.text.strip()
    if not text or text == tag['href']:
        parent.append(Command('url', tag['href']))
    else:
        parent.append(Command('href', arguments=Arguments(tag['href'], text)))

@tag_handler('img')
def img(parent, tag):
    imgpath = str(download_image(tag['src']))
    if imgpath is None:
        return
    with parent.create(Figure(position='H')) as figure:
        figure.add_image(imgpath, width=NoEscape(r'\linewidth'))

@tag_handler('u')
def underline(parent, tag):
    text = tag.text.strip()
    if text:
        parent.append(f'\\underline{text}')

@tag_handler('hr')
def hr(parent, tag):
    parent.append('\\hline')

@tag_handler('ul')
def items(parent, tag):
    with parent.create(Itemize()) as itemize:
        for li in tag.findAll('li'):
            process_tag(itemize, li)

@tag_handler('li')
def item(parent, tag):
    item_content = FlatContainer("par")
    for child in tag:
        process_tag(item_content, child)
    parent.add_item(item_content)

def process_html(doc, htmlfile):
    h2counter = 0
    with open(htmlfile) as html:
        soup = Bs(html, 'lxml')
    body = soup.html.body
    for tag in body:
        if tag.name is not None:
            if tag.name == 'h2':
                h2counter += 1
            if DEBUG and h2counter > 6:
                return
            process_tag(doc, tag)
        elif tag.string.strip():
            print('debug:', tag.string.strip())

def main():
    geometry_options = {
        "paperwidth": "4.6in",
        "paperheight": "6.2in",
        "top": "0.5cm",
        "margin": "0.5cm",
        "bottom": "15pt",
        "includefoot": True
    }
    doc = HabrBook(
        fontenc="T2A",
        inputenc=None,
        geometry_options=geometry_options)
    process_html(doc, 'flask.html')
    doc.generate_tex('test')
    with open('test.tex', 'r+') as texfile:
        text = '% TEX program = xelatex\n' + texfile.read()
        texfile.seek(0)
        texfile.write(text)


if __name__ == '__main__':
    main()
