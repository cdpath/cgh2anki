#!/usr/bin/python3
# -*- coding: utf-8 -*-

import csv
import re
import requests

from manager import Manager
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup as bs

manage_app = Manager()


def replace_with_newlines(element):
    text = ''
    for elem in element.recursiveChildGenerator():
        if isinstance(elem, str):
            text += elem.replace('\n', ' ')
        elif elem.name == 'br':
            text += '\n'
    return text.strip()


def normalize_punctuation(text):
    import unicodedata
    text = unicodedata.normalize('NFKC', text)

    import re
    tr = {
        '【': '[',
        '】': ']',
        '〔': '[',
        '〕': ']',
        '〈': '(',
        '〉': ')',
        '“': '「',
        '”': '」',
        '‘': '「',
        '’': '」',
        '⋯': '...',
    }
    pat = re.compile(u'|'.join(tr.keys()))
    text = pat.sub(lambda x: tr[x.group()], text)
    return text


def prepare_urls(start=1, step=100):
    GET_ARTICLES_URL = 'http://blog.sina.cn/dpool/blog/newblog/riaapi/mblog/get_articlelist.php'
    data = {
        'uid': 5753173330,
        'pagesize': step,
        'page': start,
        'class_id': -1,
    }
    resp = requests.post(GET_ARTICLES_URL, data=data)
    if not resp.ok:
        print("Failed to post %s with %s" % (GET_ARTICLES_URL, str(data)))
        resp.raise_for_status()
    return resp.json()['data']['msg']


def parse_url(url):
    resp = requests.get(url)
    soup = bs(resp.content, "html.parser")
    content = [
        soup.find("div", class_="content b-txt1"),
        soup.find("div", class_="item_hide")
    ]

    for c in content:
        del c['class']
    content = [replace_with_newlines(c) for c in content]
    content = [normalize_punctuation(c) for c in content]
    return ' '.join(content)


def prepare_record(content):
    pat = re.compile(r'^.*时代の句变.*\d{6}')
    del_pat = re.compile(r'^.*复习.*')
    segment = []
    lines = [i.strip() for i in content.split('\n')]
    for line in lines:
        if pat.match(line):
            if del_pat.match(line):
                continue
            yield segment
            segment = []
        segment.append(line.strip('\n'))


def parse_urls(urls):
    with ThreadPoolExecutor(1) as executor:
        results = executor.map(parse_url, urls)
    return results


def select_by(record, keyword):
    import re
    pat = re.compile(r".*(?=%s)" % keyword.replace('[', '\['))
    hits = [pat.sub('', i) for i in record if keyword in i]
    hits = [hit.replace(keyword, '') for hit in hits]
    return '<br>'.join(hits)


def run_once(f):
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
             wrapper.has_run = True
             return f(*args, **kwargs)
    wrapper.has_run = False
    return wrapper


@run_once
def write_header(f_csv):
    f_csv.writerow(('时', '事', '译', '辞', '义', '例', '评'))


def get_csv(records, output_file):
    with open(output_file, 'at') as ou_f:
        f_csv = csv.writer(ou_f)
        write_header(f_csv)
        for record in records:
            if len(record) > 1:
                t_date, t_news, t_news_zh, t_entry, t_definition, t_example, t_note = [
                    select_by(record, keyword) for keyword in [
                    '时代の句变', '[事]', '[译]', '[辞]', '[义]', '[例]', '[评]'
                ]]
                f_csv.writerow((t_date, t_news, t_news_zh, t_entry, t_definition, t_example, t_note, ))


@manage_app.command
def run(output_file):
    urls = prepare_urls()
    urls = [url['url'] for url in urls]
    results = parse_urls(urls)
    for r in results:
        records = prepare_record(r)
        get_csv(records, output_file)


if __name__ == '__main__':
    manage_app.main()

