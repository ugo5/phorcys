### bd_hotspots.py
---
百度热搜实时热点 Top10

### html2md.py
---
日常使用 markdown 来编写和摘录笔记，之前一直使用复制粘帖的方式来摘录好的网页内容。突然想到能不能用脚本来完成，这样又省去复制粘帖再排版的时间，也能把更多的时间用于阅读和理解文章内容上。

参考了 ylfeng250 的 [downloBlog](https://github.com/ylfeng250/FengTools/tree/master/downloBolg) 脚本，重新使用面向对象来重写。并且兼容了 py2 和 py3。

脚本中默认收录了几个站点，列表如下：
```
简书，知乎，CSDN，segmentfault，掘金，cnblogs
```

其他的请根据站点的实际情况来设置参数


#### 使用方法：
```
Usage:
html2md.py URL [NAME] [HTML_TAG] [CSS_SELECTOR] [RE_PATTERN] [REPL]
or: 
html2md.py --url URL [--name NAME] [--html-tag HTML_TAG] [--css-selector CSS_SELECTOR] [--re-pattern RE_PATTERN] [--repl REPL]
```

#### 参数说明：
- `URL`：blog 页面地址
- `NAME`：站点名称
- `HTML_TAG`：html 的 tag 标签
- `CSS_SELECTOR`：css 的 class 
- `RE_PATTERN`：图片 src 的原字符串
- `REPL`：图片 src 的替换字符串
