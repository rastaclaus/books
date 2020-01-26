# pylint: disable=missing-docstring
from collections import namedtuple
import re

from bs4 import BeautifulSoup as Bs

DEBUG = True

Tag = namedtuple('Tag', 'begin end')
TAGS = {
    'h1': Tag("\\title{", "}"),
    'h2': Tag("\\chapter{", "}"),
    'h3': Tag("\\section{", "}"),
    'div': Tag("", ""),
    'strong': Tag(" \\textbf{", "}"),
    'p': Tag("\n", "\n"),
    'pre': Tag("\n\\begin{lstlisting}\n", "\n\\end{lstlisting}\n"),
    'code': Tag(" \\lstinline{", '} '),
    'codein': Tag("", ''),
    'a': Tag("\ ", "\ "),
}

def process_tag(tag, inner=False):
    if tag.name == 'code' and tag.parent.name == 'pre':
        tag.name = 'codein'
    tex = TAGS.get(tag.name)
    if tex:
        print(tex.begin, end='')
    else:
        print('process tag', tag.name)

    for child in tag:
        if child.name:
            process_tag(child)
        elif child.string.strip():
            process_string(child)
    if tex:
        print(tex.end)
    else:
        print('end process tag', tag.name)

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
