# pylint: disable=missing-module-docstring, missing-function-docstring
import copy
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

URL = 'https://habr.com/en/post/346344/'


def get_fname(url):
    return urlparse(url).path[1:].replace('/', '.') + 'html'

def get_soup(url, save=True):
    fname = get_fname(url)
    try:
        with open(fname) as htmlfile:
            raw_html = htmlfile.read()
    except FileNotFoundError:
        raw_html = requests.get(url).content.decode()

    soup = BeautifulSoup(raw_html, 'lxml')

    if save is True:
        with open(fname, 'wb') as htmlfile:
            htmlfile.write(soup.prettify('utf-8'))
    return soup


def main():
    url = URL
    soup = get_soup(url)
    post = copy.copy(soup.find(id='post-content-body'))
    body = soup.html.body
    body.decompose()
    children = post.find_all_next()
    for child in children:
        if child.name:
            print (child.name)
            if child.name == 'h2':
                break
            child.decompose()

    for child in children[-3:]:
        child.decompose()
    soup.html.append(soup.new_tag("body"))
    soup.html.body.append(post)

    with open('parsed_' + get_fname(url), 'wb') as new_html:
        new_html.write(soup.prettify('utf-8'))


if __name__ == '__main__':
    main()
