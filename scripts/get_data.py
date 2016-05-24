#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'cdpath'

from urllib.request import urlopen, build_opener
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from manager import Manager
manage_app = Manager()
import json
import csv
import sys
import re


pages = set()
pat = re.compile(r'时代の句变.*\d{6}')
baseurl = 'http://blog.sina.cn/dpool/blog/newblog/riaapi/mblog/get_articlelist.php'


def get_articlelist(baseurl):
    global pages
    params = {'uid': 5753173330, 'pagesize': 100, 'page': 1, 'class_id': -1}
    params = urlencode(params)
    try:
        resp = urlopen(baseurl, params.encode('ascii'))
        resp_json = json.loads(resp.read().decode('utf-8'))
        articlelist = resp_json['data']['msg']

        for article in articlelist:
            pages.add(article.get('url'))
    except Exception as e:
        print(e)


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


def get_csv(input_file, output_file):
    def __records(input_file):
        record = list()
        with open(input_file) as f:
            while True:
                line = f.readline()
                if line:
                    if pat.match(line):
                        yield record
                        record = list()
                    record.append(line.strip('\n'))
                else:
                    break

    with open(output_file, 'wt') as f:
        f_csv = csv.writer(f)
        for record in __records(input_file):
            if len(record) > 1:
                t_date = ';'.join(filter(lambda i: i.startswith('时代'), record))
                t_news = ';'.join(filter(lambda i: i.startswith('【事】'), record))
                t_news_zh = ';'.join(filter(lambda i: i.startswith('［译］'), record))
                t_entry = ';'.join(filter(lambda i: i.startswith(('【辞】','［辞］')), record))
                t_definition = ';'.join(filter(lambda i: i.startswith(('【义】', '［义］')), record))
                t_example = ';'.join(filter(lambda i: i.startswith(('【例】', '［例］')), record))
                t_note = ';'.join(filter(lambda i: i.startswith('［评］'), record))

                f_csv.writerow((t_date, t_news, t_news_zh, t_entry, t_definition, t_example, t_note, ))


@manage_app.command
def to_read(output):
    """ download blogs """
    get_articlelist(baseurl)
    print("# Go", file=sys.stderr)

    with open(output, 'wt') as f:
        for url in pages:
            contents = parse_content(url)
            print(url, file=sys.stderr)
            for i in contents:
                try:
                    i = replace_with_newlines(i)
                    i = i.strip()
                except TypeError as e:
                    print(e)
                else:
                    f.write(i)

    print("# Done", file=sys.stderr)


@manage_app.command
def for_anki(input, output):
    """ convert to CSV to import to Anki """
    # :%s/时代の句变/\r时代の句变/g
    get_csv(input, output)


if __name__ == '__main__':
    manage_app.main()

