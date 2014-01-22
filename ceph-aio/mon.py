#encoding: utf-8

import logging
import os
import shutil
from utils import mon_data, do_cmd

LOG = logging.getLogger('ceph-aio')


def mon_install(args):
    """创建 monitor data 然后启动 monitor
    分为三步:
    1. 创建用户定义的 mon data, 并初始化这个目录
    2. 启动 ceph mon
    3. (可选) 如果用户定义了 mon data, 则必须手动获取 client.admin 的 keyring
    """

    # 创建 monitor data
    LOG.info('create mon data: %s', mon_data)
    if os.path.exists(mon_data):
        LOG.warn('mon data exists, delete it')
        shutil.rmtree(mon_data)

    os.makedirs(mon_data, mode=0700)

    # sysvint 的 ceph 启动脚本需要在 mon data 下有一个文件 sysvint, 不然不能启动
    LOG.debug('touch file sysvinit needed by ceph sysvinit script')
    open(os.path.join(mon_data, 'sysvinit'), 'w').close()

    # 初始化 monitor data
    LOG.debug('initial mon data')
    cmd = 'ceph-mon --cluster ceph --mkfs -i a --keyring /tmp/ceph.mon.keyring'
    if do_cmd(cmd)[0] != 0:
        raise RuntimeError('failed to initialize the mon data directory!')

    # 启动服务
    LOG.debug('start monitor service')
    cmd = 'service ceph -c /etc/ceph/ceph.conf start mon.a'
    if do_cmd(cmd)[0] != 0:
        raise RuntimeError('failed to start ceph monitor!')

    # 如果 mon data 是自己设置的, 不是使用默认值, 那么使用一下命令手动获取
    # client.admin keyring:
    # ceph auth --name=mon. --keyring=/var/lib/ceph/mon/ceph-a/keyring \
    # get-or-create client.admin mon 'allow *' osd 'allow *' mds 'allow *'


# monitor 要最后删除, 不然 osd 和 mds 都不能删除了 :P
def mon_clean(args):
    LOG.debug('clean ceph monitor')
    # 先结束 ceph 服务的运行
    do_cmd('service ceph -c /etc/ceph/ceph.conf stop mon.a')

    # 删除 mon data
    if os.path.exists(mon_data):
        LOG.debug('delete mon data: %s', mon_data)
        shutil.rmtree(mon_data)
    else:
        LOG.warn('mon data %s not exists', mon_data)

    # 删除配置文件和各种 keyring
    if os.path.exists('/etc/ceph/ceph.conf'):
        os.remove('/etc/ceph/ceph.conf')
    if os.path.exists('/etc/ceph/ceph.client.admin.keyring'):
        os.remove('/etc/ceph/ceph.client.admin.keyring')
    if os.path.exists('/var/lib/ceph/bootstrap-mds/ceph.keyring'):
        os.remove('/var/lib/ceph/bootstrap-mds/ceph.keyring')
    if os.path.exists('/var/lib/ceph/bootstrap-osd/ceph.keyring'):
        os.remove('/var/lib/ceph/bootstrap-osd/ceph.keyring')
