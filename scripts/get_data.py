#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from urllib.request import urlopen
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from manager import Manager
import json
import csv


manage_app = Manager()
pages = set()


def get_blog_list(baseurl):
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


def parse_content(blog_url):
    html = urlopen(blog_url)

    soup = BeautifulSoup(html, "html.parser")
    contents = soup.findAll("div", {"class": "content b-txt1"}) + soup.findAll("div", {"class": "item_hide"})
    return contents


def replace_with_newlines(element):
    text = ''
    for elem in element.recursiveChildGenerator():
        if isinstance(elem, str):
            text += elem.replace('\n', ' ')
        elif elem.name == 'br':
            text += '\n'
    return text


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


def get_csv(input_file, output_file):
    def __records(input_f):
        import re
        pat = re.compile(r'^.*时代の句变.*\d{6}')
        segment = list()
        with open(input_f) as in_f:
            while True:
                line = in_f.readline()
                if line:
                    if pat.match(line):
                        yield segment
                        segment = list()
                    segment.append(line.strip('\n'))
                else:
                    break

    def __select_by(keyword):
        import re
        pat = re.compile(r".*(?=%s)" % keyword.replace('[', '\['))
        hits = [pat.sub('', i) for i in record if keyword in i]
        return '<br>'.join(hits)

    with open(output_file, 'wt') as ou_f:
        f_csv = csv.writer(ou_f)
        f_csv.writerow(('时', '事', '译', '辞', '义', '例', '评'))
        for record in __records(input_file):
            if len(record) > 1:
                t_date = __select_by('时代の句变')
                t_news = __select_by('[事]')
                # fixme
                t_news_zh = '[' + __select_by('译]')
                t_entry = __select_by('[辞]')
                t_definition = __select_by('[义]')
                t_example = __select_by('[例]')
                t_note = __select_by('[评]')

                f_csv.writerow((t_date, t_news, t_news_zh, t_entry, t_definition, t_example, t_note, ))


@manage_app.command
def to_read(output_file):
    """download blog texts"""
    baseurl = 'http://blog.sina.cn/dpool/blog/newblog/riaapi/mblog/get_articlelist.php'
    get_blog_list(baseurl)
    logger.info("=== Start  ===")

    with open(output_file, 'wt') as f:
        for url in pages:
            contents = parse_content(url)
            logger.info("blog: %s" % url)
            for i in contents:
                try:
                    i = replace_with_newlines(i)
                    i = normalize_punctuation(i)
                    i = i.strip()
                except TypeError as e:
                    logger.error('Error Found: %s' % e)
                else:
                    f.write(i)

    logger.info("=== End ===")


@manage_app.command
def for_anki(input_file, output_file):
    """convert blog texts to CSV"""
    get_csv(input_file, output_file)


@manage_app.command
def normalize(input_file, output_file):
    """normalize Chinese punctuation"""
    with open(input_file, 'rt') as in_f, open(output_file, 'wt') as ou_f:
        while True:
            line = in_f.readline()
            if line:
                line = normalize_punctuation(line)
                line = line.strip()
                print(line, file=ou_f)
            else:
                break

if __name__ == '__main__':
    import logging
    logging.basicConfig(
        filename='anki.log',
        filemode='w',
        level=logging.INFO,
        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    )
    logger = logging.getLogger('anki')
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    logger.addHandler(ch)

    manage_app.main()
