#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import random
import re
import prettytable as pt
from bs4 import BeautifulSoup

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:49.0) Gecko/20100101 Firefox/49.0',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
]


def crawlit():
    headers = {
        'Host': 'top.baidu.com',
        'Referer': 'http://top.baidu.com',
        'Uesr-Agent': random.choice(user_agents)
    }
    url = 'http://top.baidu.com/'
    resp = requests.get(url, headers=headers)
    resp.encoding = requests.utils.get_encodings_from_content(resp.content)[0]
    html = resp.text
    soup = BeautifulSoup(html, 'html.parser')
    content = soup.find(id='hot-list')
    rank_list =[n.get_text() for n in content.find_all('span', class_=re.compile("num-*"))]
    keyword_list = [a.get_text() for a in content.find_all('a', class_='list-title')]
    keyword_href = [a['href'] for a in content.find_all('a', class_='list-title')]
    search_index = [format(int(i.get_text()), ',') for i in content.find_all('span', class_=re.compile('icon-*')) if i.get_text()]
    tb = pt.PrettyTable()
    tb.field_names = [u'排名', u'关键词', u'搜索指数', u'链接']
    for i, item in enumerate(rank_list):
        tb.add_row([item, keyword_list[i], search_index[i], keyword_href[i]])
    print(tb)


if __name__ == '__main__':
    crawlit()
