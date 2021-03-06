#!/bin/env python
# -*- coding:utf-8 -*-

import os
import sys
import requests
import random
import re
import html2text
import codecs
import fire
from bs4 import BeautifulSoup

py_version = sys.version.split()[0]
if py_version < '2.6':
    print('No support for python version: <%s>' % py_version)
    sys.exit(1)

py_version_lt3 = '2.6' <= sys.version.split()[0] < '3.0'
if py_version_lt3:
    reload(sys)
    sys.setdefaultencoding('utf-8')
    import urlparse
else:
    import urllib.parse as urlparse

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:49.0) Gecko/20100101 Firefox/49.0',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/600.7.12 (KHTML, like Gecko) Version/8.0.7 Safari/600.7.12',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
]

site_elements = {
    'cnblogs': {
        'css_selector': 'blogpost-body'
    },
    'csdn': {
        'css_selector': 'article_content'
    },
    'jianshu': {
        'html_tag': 'section',
        're_pattern': '(src=")|(data-original-src=")',
        'repl': 'src="https:',
        'css_selector': 'ouvJEz'
    },
    'juejin': {
        'css_selector': 'entry-content'
    },
    'segmentfault': {
        're_pattern': 'data-src="',
        'repl': 'src="https://segmentfault.com',
        'css_selector': 'article__content'
    },
    # 淘股吧
    'taoguba': {
        'css_selector': 'p_coten'
    },
    # 拾荒网
    '10huang': {
        'css_selector': 'hl_body'
    },
    # 360doc
    '360doc': {
        'html_tag': 'td',    
        'id_selector': 'artContent'
    },
    'zhihu': {
        # 'html_tag': 'div',
        'css_selector': 'Post-RichText'
    },
}


class HtmlToMd(object):
    def __init__(self):
        self.url = ''
        self.site = ''
        self.scheme = 'http'

    @staticmethod
    def header(url):
        """请求头信息"""
        url_segment = urlparse.urlsplit(url)
        host = url_segment.netloc
        site = host.split('.')[1]
        scheme = url_segment.scheme
        referer = '%s://%s' % (scheme, host)
        _header = {
            'Host': host,
            'Referer': referer,
            'User-Agent': random.choice(user_agents)
        }
        return scheme, site, _header

    @staticmethod
    def write2md(url, dir_path, title, article):
        """将解析后的 html 保存为 .md 文件"""
        ## 创建转换器
        h2md = html2text.HTML2Text()
        h2md.ignore_links = False
        ## 转换文档
        article = h2md.handle(article)
        ## 写入文件
        # 判断目录是否存在，不存在则创建新的目录
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        # 创建md文件, 使用 codecs 兼容 py2
        md_file = os.path.join(dir_path, title + '.md')
        with codecs.open(md_file, 'w', encoding="utf8") as f:
            f.write('参考：%s\n\n---\n' % url)
            lines = article.splitlines()
            for line in lines:
                if line.endswith('-'):
                    f.write(line)
                else:
                    f.write(line + "\n")
        print("-----"*10)
        print("== 下载完成: [%s]" % title)
        print("== 文件目录: [%s]" % dir_path)

    def get_site(self, url, name=None, html_tag=None,
                 css_selector=None, id_selector=None, 
                 re_pattern=None, repl=None):
        """
        :param url: 需要下载的 url
        :param name:  站点名称，也是本地保存的目录名
        :param html_tag: html 元素 tag
        :param re_pattern: 图片 src 替换的正则表达式
        :param repl: 替换的字符串
        :param css_selector: 过滤的 css class
        :return: 
        """
        ## 获取网页主体
        self.url = url
        self.scheme, self.site, _headers = self.header(self.url)
        html = requests.get(self.url, headers=_headers).content
        name = self.site if not name else name
        for _site in site_elements.keys():
            if self.site.find(_site) != -1:
                name = _site
        if name == 'segmentfault' and url.split('/')[3] != 'a':
            return 'Segmentfault url not support, please check url with /a/'
        if name in site_elements:
            html_tag = site_elements.get(name).get('html_tag')
            if html_tag == None:
                html_tag = 'div'
            if css_selector == None:
                css_selector = site_elements.get(name).get('css_selector')
            if id_selector == None:
                id_selector = site_elements.get(name).get('id_selector')
            if re_pattern == None:
                re_pattern = site_elements.get(name).get('re_pattern')
            if repl == None:
                repl = site_elements.get(name).get('repl')
        ## bs4
        parser = 'html.parser' if name == 'juejin' else 'html5lib'
        # parser = 'html.parser'
        soup = BeautifulSoup(html, parser)
        title = soup.find_all("title")[0].get_text()
        if name == 'taoguba':
            title = title.split('_',1)[0]
        elif name == '10huang':
            title = title.split(u'_拾荒网')[0]
        article = str(soup.body)
        # print soup.find_all(class_='ouvJEz')
        if html_tag and css_selector:
            article = str(soup.find_all(html_tag, class_=css_selector)[0])
        elif html_tag and id_selector:
            article = str(soup.find_all(html_tag, id=id_selector)[0])
        elif html_tag:
            article = str(soup.find_all(html_tag)[0])
        elif css_selector:
            article = str(soup.find_all(class_=css_selector)[0])
        ## 替图片的src加上https://(http://), 方便访问
        if re_pattern and repl:
            article = re.sub(re_pattern, repl, article)
        ## 写入文件
        # pwd = os.getcwd()
        pwd = os.path.dirname(os.path.abspath(__file__))
        dir_path = os.path.join(pwd, name)
        self.write2md(url, dir_path, title.strip(), article)


if __name__ == '__main__':
    h2m = HtmlToMd()
    fire.Fire(h2m.get_site)
