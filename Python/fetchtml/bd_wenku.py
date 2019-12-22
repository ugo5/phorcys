# -*- coding:utf-8 -*-
import sys
import requests
import json
import re
import os
import fire
from docx import Document

reload(sys)
sys.setdefaultencoding('utf-8')


def get_document(url):
    """Get document from bd wenku"""
    sess = requests.Session()
    html = sess.get(url).content.decode("gbk")

    # Get the title
    title = re.search('id="doc-tittle-0">(.*?)</span>', html).group(1)
    # 使用正则提取 文档内容的url
    res = re.search("WkInfo.htmlUrls = '(.*)'", html).group(1)
    # \\x22是linux中的引号，替换成Python中的引号
    res = res.replace("\\x22", "\"")
    # 转成字典
    data = json.loads(res)

    # new word document
    document = Document()
    string = ""
    for i in data["json"]:
        # Get url and replace
        url = i["pageLoadUrl"]  
        url = url.replace("\\", "")
        # Get content
        data = requests.get(url).content.decode("utf-8")
        # 提取文本数据
        res = re.search("wenku_\d*\((.*)\)", data, re.S).group(1)
        data = json.loads(res)
        for i in data['body']:
            # 判断数据是什么类型
            if i["t"] == "word":
                # 获取到文本
                string += str(i["c"])
                # ps中不为空并且_enter==1的时候是换行也就是一段内容
                if i["ps"] and i["ps"].get("_enter") == 1:
                    # 将一段内容写入到word
                    document.add_paragraph(unicode(string))
                    # 重新复制 "" 表示新的一段文本
                    string = ""  
    # 保存word
    document.save(title + ".docx")
    print(u'===下载成功===')
    print(u'===目录: '+os.getcwd())

if __name__ == '__main__':
    fire.Fire(get_document)
