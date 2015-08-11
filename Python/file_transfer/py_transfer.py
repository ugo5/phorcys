#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: uchen
# Version: __0.2__
# Create: 08/11 2015

import os
import time
import sys
from hashlib import md5
from optparse import OptionParser
import ConfigParser
try:
    import paramiko
except ImportError:
    print('No paramiko module, please install it.')


## Get file md5sum code
def get_md5(full_filename):
    _md5 = md5()
    filename = file(full_filename, 'rb')
    _md5.update(filename.read())
    filename.close()
    return _md5.hexdigest()


## Execute command on remote host
def exec_cmd(hostname, port=22, username=None, password=None, command=None):
    '''Execute command on a remote host'''
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password)
        stdin, stdout, stderr = ssh.exec_command(command)
        return stdout.read()
        ssh.close()
    except:
        return '[Error] please check connection information of remote host'


def pkg_transfer(action, section):
    '''Deploy the update packages to application server'''
    if action not in ['upload', 'download']:
        print('[Error] No action: "%s"' % action)
        sys.exit(10)
    try:
        hosts = cf.get(section, 'host')
        try:
            port = int(cf.get(section, 'port'))
        except:
            port = 22
        username = cf.get(section, 'username')
        password = cf.get(section, 'passw0rd')
        local_res = cf.get(section, 'local_res')
        remote_res = cf.get(section, 'remote_res')
    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError) as e:
        print('[Error] ' + str(e))
        sys.exit(11)

    for hostname in hosts.split(','):
        pa_t = paramiko.Transport((hostname, port))
        pa_t.connect(username=username, password=password)
        pa_sftp = paramiko.SFTPClient.from_transport(pa_t)
        try:
            r_stat = pa_sftp.stat(remote_res).__str__()
        except IOError, e:
            print e
            sys.exit(12)

        print('##'*8 + '[%s]' % hostname)
        print('[%s] Beginning to %s files.' % (time.strftime("%Y-%m-%d %H:%M:%S"), action))

        ## local_res and remote_res are directorys
        if os.path.isdir(local_res) and r_stat.startswith('d'):
            if action == 'upload':
                up_files = filter(lambda f: not f.startswith('.'), os.listdir(local_res))
                if len(up_files) != 0:
                    for u_f in up_files:
                        print('%sing file: [%s] ' % (action, os.path.join(local_res, u_f)))
                        pa_sftp.put(os.path.join(local_res, u_f), os.path.join(remote_res, u_f))
                    log_info = '[%s] %s files success.' % (time.strftime("%Y-%m-%d %H:%M:%S"), action)
                else:
                    log_info = '%s directory is empty, no file %s' % (local_res, action)
            else:
                down_files =  filter(lambda f: not f.startswith('.'), pa_sftp.listdir(remote_res))
                if len(down_files) != 0:
                    for d_f in down_files:
                        print('%sing file: [%s] ' % (action, os.path.join(remote_res, d_f)))
                        pa_sftp.get(os.path.join(remote_res, d_f), os.path.join(local_res, d_f))
                    log_info = '[%s] %s files success.' % (time.strftime("%Y-%m-%d %H:%M:%S"), action)
                else:
                    log_info = '%s directory is empty, no file %s' % (remote_res, action)
        ## local_res is a directory, and remote_res is a file
        elif os.path.isdir(local_res) and r_stat.startswith('-'):
            if action == 'upload':
                log_info = '[Error] %s is a file , can\'t %s directory to the file' % (remote_res, action)
            else:
                print('%sing file: [%s] ' % (action, remote_res))
                pa_sftp.get(remote_res, os.path.join(local_res, os.path.basename(remote_res)))
                log_info = '[%s] %s files success.' % (time.strftime("%Y-%m-%d %H:%M:%S"), action)
        ## local_res is a file, and remote_res is a directory
        elif os.path.isfile(local_res) and r_stat.startswith('d'):
            if action == 'upload':
                local_res_md5 = get_md5(local_res)
                remote_res_md5 = exec_cmd(hostname, port, username, password,\
                                          "md5sum %s |awk 'BEGIN {ORS=\"\"} {print $1}'" % os.path.join(remote_res, os.path.basename(local_res)))
                if local_res_md5 == remote_res_md5:
                    print('[Attention] Transfer files no change, nothing to do.')
                    sys.exit(13)
                else:
                    print('%sing file: [%s] ' % (action, local_res))
                    pa_sftp.put(local_res, os.path.join(remote_res, os.path.basename(local_res)))
                    log_info = '[%s] %s files success.' % (time.strftime("%Y-%m-%d %H:%M:%S"), action)
            else:
                log_info = '[Error] %s is a file , can\'t %s directory to the file' % (local_res, action)
        ## local_res and remote_res are files
        elif os.path.isfile(local_res) and r_stat.startswith('-'):
            local_res_md5 = get_md5(local_res_md5)
            remote_res_md5 = exec_cmd(hostname, port, username, password, \
                                      "md5sum %s |awk 'BEGIN {ORS=\"\"} {print $1}'" % remote_res)
            if local_res_md5 == remote_res_md5:
                print('[Attention] Transfer files no change, nothing to do.')
                sys.exit(13)
            if action == 'upload':
                print('%sing file: [%s] ' % (action, local_res))
                pa_sftp.put(local_res, remote_res)
                log_info = '[%s] %s files success.' % (time.strftime("%Y-%m-%d %H:%M:%S"), action)
            else:
                print('%sing file: [%s] ' % (action, remote_res))
                pa_sftp.get(remote_res,local_res)
                log_info = '[%s] %s files success.' % (time.strftime("%Y-%m-%d %H:%M:%S"), action)
        ## other options is error
        else:
            log_info = '[Error] no such %s and %s , please your configuration file!' % (local_res, remote_res)

        pa_t.close()
        print(log_info)
        print('##'*8)


if __name__ == '__main__':
    '''Use optparse module for command line help information'''
    usage = 'usage: %prog -a <upload or download> -s <section> [-l]'
    parser = OptionParser(usage=usage)
    parser.add_option("-a", "--action", dest="action", help="action you want to do, only [upload/download]")
    parser.add_option("-s", "--section", dest="section", help="section part of you choose")
    parser.add_option("-l", "--list", action="store_true", dest="sections", help="list available in the section")
    (options, args) = parser.parse_args()

    cf = ConfigParser.SafeConfigParser()
    cf.read('transfer.conf')
    if options.sections:
        print('Available sctions :')
        for s_ in cf.sections():
            print(s_)
        sys.exit(0)

    logfile = os.path.dirname(os.path.abspath(__file__)) + '/transfer.log'

    if len(sys.argv[1:]) == 0:
        parser.print_help()
    else:
        pkg_transfer(options.action, options.section)
