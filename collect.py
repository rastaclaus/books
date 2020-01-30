# pylint: disable=missing-module-docstring, missing-function-docstring
import copy
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

URL = 'https://habr.com/ru/post/309958/'
HEADERS = re.compile('^h[1-6]$')

def get_fname(url):
    return urlparse(url).path[1:].replace('/', '.') + 'html'

def get_table_of_content(post):
    toc_container = post.find(name='div', attrs={'class': 'spoiler'})
    ul_tag = toc_container.ul
    result = dict()
    for a_tag in ul_tag.find_all('a', href=True)[1:]:
        result[a_tag['href']] = a_tag.strong.text.strip()
    return result

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


def shift_headers(soup, post):
    for header in post.find_all(HEADERS):
        new_header = soup.new_tag('h' + str(int(header.name[-1])+1))
        new_header.append(header.text)
        header.replace_with(new_header)

def strip_post(soup, post, last_post=False):
    children = post.find_all_next()
    for child in children:
        if child.name:
            if child.name == 'h2' and child.text.strip() != "(издание 2018)":
                print(child.text)
                break
            child.decompose()

    if not last_post:
        p_tag = post.find_all('p')[-1]
        p_tag.decompose()
    for br_tag in post.find_all('br'):
        br_tag.decompose()
    shift_headers(soup, post)


def main():
    #TODO dict unneed!
    url = URL
    soup = get_soup(url)
    post = copy.copy(soup.find(id='post-content-body'))
    toc = {url: 'React.js: собираем с нуля изоморфное / универсальное приложение. Часть 1: собираем стек'}
    # toc.update(get_table_of_content(post))
    for script_tag in soup.html.head.find_all(name='script'):
        script_tag.decompose()
    body = soup.html.body
    body.decompose()
    soup.html.append(soup.new_tag("body"))
    h1_tag = soup.new_tag('h1')
    h1_tag.append('React.js: собираем стек')
    soup.html.body.append(h1_tag)
    # dirty fix
    last=False
    for link, title_text in toc.items():
        print(title_text)
        if "23" in title_text:
            last = True
        page = get_soup(link)
        post = copy.copy(page.find(id='post-content-body'))
        strip_post(soup, post, last)
        h2_tag = soup.new_tag('h2')
        h2_tag.append(title_text)
        soup.html.body.append(h2_tag)
        soup.html.body.append(post)

    with open('react.html', 'wb') as new_html:
        new_html.write(soup.prettify('utf-8'))

if __name__ == '__main__':
    main()
