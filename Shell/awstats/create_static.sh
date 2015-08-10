#!/bin/bash  
# The Nginx logs path  
logs_names=(access_www access_img)     #log的名称  
web_path="/var/www/awstats"            #静态html的路径  
cgi_path="/usr/share/awstats/wwwroot/cgi-bin"  #awstats可执行文件的存放路径  
static_path="/usr/share/awstats/tools"         #awstats可执行文件的存放路径  
num=${#logs_names[@]}  
for((i=0;i<num ;i++));do  
    if [ ! -d ${web_path}/${logs_names[i]} ]  
    then  
        mkdir -p ${web_path}/${logs_names[i]}  
    fi  
    ${static_path}/awstats_buildstaticpages.pl -update \  
    -config=${logs_names[i]} -lang=cn -dir=${web_path}/${logs_names[i]} \  
    -awstatsprog=${cgi_path}/awstats.pl  
done
