#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'cdpath'

from urllib.request import urlopen, build_opener
from urllib.parse import urlencode
from bs4 import BeautifulSoup
import json
baseurl = 'http://blog.sina.cn/dpool/blog/newblog/riaapi/mblog/get_articlelist.php'
pages = set()


def get_articlelist(BaseUrl):
    global pages
    params = {'uid': 5753173330, 'pagesize': 100, 'page': 1, 'class_id': -1}
    params = urlencode(params)
#    params = 'uid=5753173330&pagesize=100&page=1&class_id=-1'
    try:
        resp = urlopen(BaseUrl, params.encode('ascii'))
        resp_json = json.loads(resp.read().decode('utf-8'))
        articlelist = resp_json['data']['msg']
    except Exception as e:
        print(e)

    for article in articlelist:
        #print(article)
        pages.add(article.get('url'))


def parse_content(Url):
#    html = urlopen(Url)
    opener = build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1')]
    html = opener.open(Url)

    bsObj = BeautifulSoup(html, "html.parser")
    contents = bsObj.findAll("div", {"class": "content b-txt1"}) + bsObj.findAll("div", {"class": "item_hide"})
    return contents


def replace_with_newlines(element):
    text = ''
    for elem in element.recursiveChildGenerator():
        if isinstance(elem, str):
            text += elem.replace('\n', '')
        elif elem.name == 'br':
            text += '\n'
    return text


def main():
    get_articlelist(baseurl)

    for url in pages:
        contents = parse_content(url)
        print(url)
        for i in contents:
            try:
                i = replace_with_newlines(i)
                i = i.strip()
            except TypeError as e:
                print(e)
            else:
                print(i),


if __name__ == '__main__':
    main()

