#!/bin/bash
## purpose: Deploy scripts for rpd advert
## author: uchen
set -e

## Your package name
PKG_NAME="xxx.war"
## Location of your update package on server, like "/opt/update-pkgs"
UPPKG_DIR="xxx/xxx"
## Location of backups, like "/opt/backups"
BAK_DIR="xxx/xxx"
## Path of your website document root, like "/var/www/root"
SRC_DIR="xxx/xxx"
LOG="$(cd `dirname $0`;pwd)/deploy.log"

[[ -z $UPPKG_DIR/$PKG_NAME ]] && (echo -e "\033[31m[Error:]\033[0m No specify the packge name"; exit 9) 

if [[ "$PKG_NAME" =~ \.war$ ]];then
    BAK_PKG="$PKG_NAME-$(date +%Y%m%d)"
else
    ## Get the PKG_NAME prefix part
    BAK_PKG="${PKG_NAME%.*}-$(date +%Y%m%d).tar.gz"
fi

## Function for pring logs to a file
function LogPrint()
{    
    ## $1 is log title, $2 is logfile    
    echo -e "[$(date '+%Y%m%d %H:%M:%S')] $1 \n------" >> $2
}

## Check whether there is above directory
if [[ ! -d $UPPKG_DIR ]];then
    mkdir -p $UPPKG_DIR
    LogPrint "Create $UPPKG_DIR success" $LOG
fi

if [[ ! -d $BAK_DIR ]];then
    mkdir -p $BAK_DIR
    LogPrint "Create $BAK_DIR success" $LOG
fi

if [[ ! -d $SRC_DIR ]];then
    LogPrint "[Err] $SRC_DIR not exist" $LOG
    echo -e "\033[31m[Error:]\033[0m Please see log for more"
    exit 10;
fi


## Backups website function
function Backups()
{
    if [[ ! -e "$BAK_DIR/$BAK_PKG" ]];then
    	LogPrint "Enter $SRC_DIR" $LOG
   	cd $SRC_DIR

    	LogPrint "Backups the website codes to $BAK_DIR" $LOG 
    	if [[ "$BAK_PKG" =~ \.tar.gz$ ]];then
            [[ ! -e ${PKG_NAME%.*} ]] && (echo -e "\033[31m[Error:]\033[0m No update site directory"; exit 11)
            tar czvf $BAK_DIR/$BAK_PKG ${PKG_NAME%.*}/* >> $LOG
        else
    	    /bin/cp -v $PKG_NAME $BAK_DIR/$BAK_PKG >> $LOG
    	fi

    else
       echo -e "\033[33m[Tips:]\033[0m The $BAK_PKG has exist!"
    fi
}


## Update website code function
function Update()
{
    if [[ -e "$BAKDIR/$BAKPKG" ]]; then
        echo -e "[$(date '+%Y%m%d %H:%M:%S')] Enter $SRC_DIR \n------" >> $LOG
        cd $SRC_DIR

        echo -e "[$(date '+%Y%m%d %H:%M:%S')] Delete unpacked directory \n------" >> $LOG
        ls -F |grep '/$' >> $LOG
        ls -F |grep '/$' |xargs rm -r
        /bin/cp $UPPKG_DIR/$PKG_NAME .
    else
        exit 11;
    fi
    
}

function RestartTomcat()
{
    ## Location of tomcat
    TOMCAT_DIR="/usr/local/tomcat" 
    TOMCAT_LOG="$TOMCAT_DIR/logs/catalina.out" 

    ## Kill java process
    if [[ `ps -ef |grep [ja]va |wc -l` ]];then
        pkill -9 java
    fi
    cd $TOMCAT_DIR

    ## Delete temp cache files
    if [[ -e "$TOMCAT_DIR" ]];then
        rm -rf $TOMCAT_DIR/temp/*
        rm -rf $TOMCAT_DIR/work/* 
    else
        echo "$TOMCAT_DIR no exist!"
        exit 12;
    fi

    ## Start tomcat and tailf logs
    $TOMCAT_DIR/bin/startup.sh && tailf $TOMCAT_LOG
}

## main execution
Backups
Update
RestartTomcat

## End, close set
set +e
