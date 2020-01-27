# pylint: disable=missing-docstring
from collections import namedtuple
import re

from bs4 import BeautifulSoup as Bs
from html2tex import HabrBook, Lstlisting, Section, Subsection, Command

DEBUG = True

TAGS = {
}

def process_tag(doc, tag, inner=False):
    handler = TAGS.get(tag.name)
    if handler:
        print(handler(tag))
    else:
        print('unknown tag', tag.name)

    for child in tag:
        if child.name:
            process_tag(doc, child)
        elif child.string.strip():
            process_string(child)

def process_string(tag):
    print(tag.string.strip(), end='')

def process_html(htmlfile):
    h2counter=0
    with open(htmlfile) as html:
        soup = Bs(html, 'lxml')
    body = soup.html.body
    for tag in body:
        if tag.name is not None:
            if tag.name == 'h2':
                h2counter += 1
            if DEBUG and h2counter > 1:
                return
            process_tag(tag)
        elif tag.string.strip():
            print('debug:', tag.string.strip())
            process_string(tag)


def main():
    htmlfile = 'flask.html'
    process_html(htmlfile)

if __name__ == '__main__':
    main()
