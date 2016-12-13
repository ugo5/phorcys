#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: ugo5
# Date: 2016-12-2

import os
import platform
import socket
import glob
import urllib2
import logging
from logging.handlers import RotatingFileHandler
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

try:
    import json
    # Detect python-json which is incompatible and fallback to simplejson in
    # that case
    try:
        json.loads
        json.dumps
    except AttributeError:
        raise ImportError
except ImportError:
    import simplejson as json

SYSTEM = platform.system()
if SYSTEM.lower() == 'linux':
    import fcntl
    import struct
if SYSTEM.lower() == 'windows':
    try:
        import wmi
    except AttributeError:
        raise ImportError

# 脚本路径
DIR_ROOT = os.path.dirname(os.path.abspath(__file__))
# 定义机房
IDC_LIST = {'HZ':u'杭州', 'WH':u'武汉', 'JH':u'金华'}


class Logger(object):
    '''Use logging module to manager logs'''
    # 0-NOTSET, 10-DEBUG, 20-INFO, 30-WARNING, 40-ERROR, 50-CRITICAL
    FORMAT_DICT = {
        0 : logging.Formatter('[%(asctime)s %(name)s %(levelname)s] - %(message)s'),
        10 : logging.Formatter('[%(asctime)s %(name)s %(levelname)s] - %(message)s'),
        20 : logging.Formatter('[%(asctime)s %(name)s %(levelname)s] - %(message)s'),
        30 : logging.Formatter('[%(asctime)s %(name)s %(levelname)s] - %(message)s'),
        40 : logging.Formatter('[%(asctime)s %(name)s %(levelname)s] - %(message)s'),
        50 : logging.Formatter('[%(asctime)s %(name)s %(levelname)s] - %(message)s'),
    }

    def __init__(self, log_name, log_level=10, logger=''):
        # Create a logger
        self.log_name = log_name
        self.log_level = log_level
        self.logger = logging.getLogger(logger)
        self.logger.setLevel(logging.INFO)
        self.formatter = self.FORMAT_DICT[int(self.log_level)]

    # output to circle file
    def rotating_file(self, size, count):
        Rthandler = RotatingFileHandler(self.log_name,
                                        maxBytes=size*1024*1024,
                                        backupCount=count)
        Rthandler.setLevel(self.log_level)
        Rthandler.setFormatter(self.formatter)
        self.logger.addHandler(Rthandler)
        return self.logger

    # output to console
    def console_out(self):
        Strhandler = logging.StreamHandler()
        Strhandler.setLevel(self.log_level)
        Strhandler.setFormatter(self.formatter)
        self.logger.addHandler(Strhandler)
        return self.logger

# --------------------------------------------------

class Factors(object):
    '''Get basic platform factors'''
    def __init__(self, load_on_init=True):
        self.factors = {}
        self.hostname = platform.node().split('.')[0]
        self.factors['hostname'] = self.hostname
        if load_on_init:
            self.get_location()
            self.get_belong_app()
            self.get_cpu()

    # 获取位置信息
    def get_location(self):
        lab_name = IDC_LIST.get('HZ')
        if self.hostname.startswith('WH'):
            lab_name = IDC_LIST.get('WH')
        if self.hostname.startswith('JH'):
            lab_name = IDC_LIST.get('JH')
        self.factors['labName'] = lab_name

    # 获取主机所归属的应用
    def get_belong_app(self):
        application = self.hostname
        for _pre in IDC_LIST.keys():
            if self.hostname.startswith(_pre):
                application = self.hostname.split('-')[1]
        self.factors['belongToApp'] = application

    # 获取 CPU 信息
    def get_cpu(self):
        from multiprocessing import cpu_count
        self.factors['cpuMsg'] = str(cpu_count())

    def populate(self):
        return self.factors


class LinuxHardware(Factors):
    '''Linux hardware information, such as cpu, memory or disk'''
    def __init__(self):
        Factors.__init__(self)

    def populate(self):
        self.get_device_virtual()
        # self.get_cpu()
        self.get_memory()
        self.get_disk()
        self.get_network()
        return self.factors

    # 获取 device virtual 信息
    def get_device_virtual(self):
        self.factors['kernelVersion'] = platform.release()
        self.factors['osType'] = '-'.join(platform.dist())
        if os.path.exists('/sys/devices/virtual/dmi/id/product_name'):
            product_name = get_file_content('/sys/devices/virtual/dmi/id/product_name')
            sys_vendor = get_file_content('/sys/devices/virtual/dmi/id/sys_vendor')
            self.factors['deviceCategory'] = '%s %s' % (sys_vendor, product_name)
            self.factors['serialNum'] = get_file_content('/sys/devices/virtual/dmi/id/product_serial')
            self.factors['machineCategory'] = u'虚拟机' if 'VMware,' in sys_vendor else u'物理机'
            self.factors['deviceType'] = u'服务器'

    # 获取内存信息
    def get_memory(self, default=None):
        if not os.access("/proc/meminfo", os.R_OK):
            return

        for line in get_file_lines("/proc/meminfo"):
            data = line.split(":", 1)
            # Once find memtotal ,break for circle
            if line.startswith('MemTotal:'):
                default = pretty_bytes(float(data[1].strip().split()[0]) * 1024)
                break
        self.factors['menMsg'] = default

    # 获取硬盘信息
    def get_disk(self):
        sys_blk = '/sys/block'
        try:
            block_devs = os.listdir(sys_blk)
        except OSError:
            return

        disk_msg = 'No device'
        device =[]
        for block in block_devs:
            try:
                path = os.readlink(os.path.join(sys_blk, block))
            except:
                continue
            # exclude virtual devices and srX devices
            if '/devices/virtual' in path or block.startswith('sr'):
                continue

            # get block sectors
            sectors = get_file_content('%s/%s/size' % (sys_blk, block), 0)
            # get block sectorsize
            sector_size = get_file_content(
                '%s/%s/queue/physical_block_size' % (sys_blk, block)
            )
            if not sector_size:
                sector_size = get_file_content(
                    '%s/%s/queue/hw_sector_size' % (sys_blk, block), 512
                )
            size = pretty_bytes((float(sectors) * float(sector_size)))
            device.append('%s-%s' % (block, size))

        if device:
           disk_msg = ','.join(device)

        self.factors['diskMsg'] = disk_msg

    # 获取网络信息
    def get_network(self):
        '''
        Get network information, format:
        - 'ip':'eth0-192.168.x.x,eth1:192.168.x.xx'
        - 'mac':'eth0-aa:bb:cc:ee:dd:ff'
        '''
        net_pre = '/sys/class/net'
        # get active net interface cards
        active_nics = [ nic.split('/')[-2]
                        for nic in glob.glob('%s/*/operstate' % net_pre)
                        if get_file_content(nic).lower() == 'up' ]
        ip_info_list = map(lambda x:
                           '%s-%s' % (x, get_linux_address(x)),
                           active_nics)
        mac_info_ist = map(lambda x:
                           '%s-%s' % (x,
                                      get_file_content('%s/%s/address' %
                                                       (net_pre, x))),
                           active_nics)
        self.factors['ip'] = ','.join(ip_info_list)
        self.factors['macMsg'] = ','.join(mac_info_ist)


class WindowsHardware(Factors):
    '''Windows hardware information, such as cpu, memory or disk'''
    def __init__(self):
        Factors.__init__(self)

    def populate(self):
        self.get_device_virtual()
        return self.factors

    # 获取 device virtual 信息
    def get_device_virtual(self):
        self._platform = platform.platform()
        self.factors['kernelVersion'] = self._platform.split('-',2)[-1]
        self.factors['osType'] = '-'.join(self._platform.split('-',2)[0:2])

        c = wmi.WMI()
        # Device information
        self.computer_sys = c.Win32_ComputerSystem()[0]
        self.factors['deviceCategory'] = '%s %s' % (
            self.computer_sys.Manufacturer,
            self.computer_sys.Model
            )
        self.factors['machineCategory'] = u'虚拟机' \
            if 'VMware,' in self.computer_sys.Manufacturer \
            else u'物理机'
        self.factors['deviceType'] = u'服务器'

        # Memory information
        total_mem = self.computer_sys.TotalPhysicalMemory
        self.factors['menMsg'] = pretty_bytes(float(total_mem))

        # Disk information
        total_disk = c.Win32_DiskDrive()[0].Size
        self.factors['diskMsg'] = pretty_bytes(float(total_disk))


        # Network information
        mac_list = []
        ip_list = []
        for interface in c.Win32_NetworkAdapterConfiguration(IPEnabled=1):
            mac_list.append(interface.MACAddress)
            ip_list.append(list(interface.IPAddress)[0])
        self.factors['ip'] = ','.join(ip_list)
        self.factors['macMsg'] = ','.join(mac_list)

# --------------------------------------------------

# 日志输出
logger = Logger(os.path.join(DIR_ROOT, 'logger.log'), 20).rotating_file(10, 3)
logger_console = Logger(os.path.join(DIR_ROOT, 'logger.log'), 30).console_out()

def get_file_content(path, default=None, strip=True):
    '''get file content with path parameter'''
    data = default
    if os.path.exists(path) and os.access(path, os.R_OK):
        with open(path) as datafile:
            data = datafile.read()
            if strip:
                data = data.strip()
            if len(data) == 0:
                data = default
    return data

def get_file_lines(path):
    '''file.readlines() that closes the file'''
    with open(path) as datafile:
        return datafile.readlines()

def get_address():
    '''Get ip address through socket.gethostname()'''
    try:
        host_name = socket.getfqdn(socket.gethostname())
        address = socket.gethostbyname(host_name)
    except:
        address = 'none resolvable hostname'
    return address

def pretty_bytes(size):
    ranges = (
        (1 << 70L, 'ZB'),
        (1 << 60L, 'EB'),
        (1 << 50L, 'PB'),
        (1 << 40L, 'TB'),
        (1 << 30L, 'GB'),
        (1 << 20L, 'MB'),
        (1 << 10L, 'KB'),
        (1, 'Bytes')
    )
    for threshold, suffix in ranges:
        if size >= threshold:
            break
    return '%.2f %s' % (float(size) / threshold, suffix)

def factors(system):
    factors = {}
    system = system.lower()
    factors.update(Factors().populate())
    if system == 'linux':
        factors.update(LinuxHardware().populate())
    if system == 'windows':
        factors.update(WindowsHardware().populate())
    return factors

def post_agent(url, data):
    response = None
    headers = {
        'Content-Type': 'application/json',
        'Accept': '*/*'
        }
    j_data = json.dumps(data)
    logger.info(j_data)
    try:
        request = urllib2.Request(url, j_data, headers)
        response = urllib2.urlopen(request, timeout=2)
    except urllib2.URLError, e:
        logger.warn(str(e))
    if response and response.read():
        logger.info('Post success!')
    else:
        logger.error('Post failed!')
    # return response.read() and response

#-----------------------------------------------

if __name__ == '__main__':
    url = 'http://cmdb.example.com/admin/api/v1/submitcmdbmsg'
    post_agent(url, factors(SYSTEM))
