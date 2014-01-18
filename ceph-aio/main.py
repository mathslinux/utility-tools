#encoding: utf-8

"""
ceph-aio: deploy ceph all in one
usage:
  ceph-aio install
  ceph-aio clean
  ceph-aio -h
"""

import sys
import os
import argparse
from ConfigParser import ConfigParser
import uuid
import struct
import time
import base64
import commands
import logging
import exc
import shutil

LOG = logging.getLogger(__name__)

# TODO: let user decides ceph_data
# TODO: 解释为什么 ceph_data 一定要是这个
ceph_data = '/var/lib/ceph'
mon_data = os.path.join(ceph_data, 'mon/ceph-a')


def get_ip(args):
    """由于是单机版, 直接返回 lo 的地址
    """
    return '127.0.0.1'


def pkg_install(args):
    # TODO
    pass


# stole from ceph-deploy
def generate_auth_key():
    key = os.urandom(16)
    header = struct.pack(
        '<hiih',
        1,                 # le16 type: CEPH_CRYPTO_AES
        int(time.time()),  # le32 created: seconds
        0,                 # le32 created: nanoseconds,
        len(key),          # le16: len(key)
    )
    return base64.b64encode(header + key)


def gen_config(args):
    """生成配置文件 /etc/ceph/client.conf 和密钥文件 ceph.mon.keyring

    配置文件如下:
    [global]
    auth service required = cephx
    auth client required = cephx
    auth cluster required = cephx
    fsid = 7b9c5452-8599-48ac-b7cb-d7d6d36b53d2
    mon initial members = a
    mon host = 192.168.176.37
    mon data = /root/ceph/mon/$cluster-$id
    filestore xattr use omap = true
    """
    cfg = ConfigParser()
    cfg.add_section('global')

    # 认证设置, 没有什么好说的, 目前 ceph 仅仅支持 cephx 方式
    cfg.set('global', 'auth service required', 'cephx')
    cfg.set('global', 'auth client required', 'cephx')
    cfg.set('global', 'auth cluster required', 'cephx')

    # fsid
    fsid = uuid.uuid4()
    cfg.set('global', 'fsid', str(fsid))

    # monitor 设置
    # 由于是单机部署环境, 只有一个 monitor 成员, 这里把 monitor ID 设为 a,
    # 设置 monitor member 的网络地址
    cfg.set('global', 'mon initial members', 'a')
    cfg.set('global', 'mon host', get_ip(args))
    cfg.set('global', 'mon data', mon_data)

    # OSD 设置, xfs 和 btrfs 需要 omap 选项
    cfg.set('global', 'filestore xattr use omap', 'true')

    LOG.debug('generating ceph config file /etc/ceph/ceph.conf')
    try:
        with file('/etc/ceph/ceph.conf', 'w') as f:
            cfg.write(f)
    except:
        raise RuntimeError('failed to create ceph config /etc/ceph/ceph.conf')

    LOG.debug('generating monitor keyring file')
    keyring = '/tmp/ceph.mon.keyring'
    try:
        with file(keyring, 'w') as f:
            f.write('[mon.]\nkey = %s\ncaps mon = allow *\n'
                    % generate_auth_key())
    except:
        raise RuntimeError('failed to create keyring file %s' % (keyring))


def do_cmd(cmd):
    LOG.debug('execute command: "%s"', cmd)
    (status, out) = commands.getstatusoutput(cmd)
    for i in out.split('\n'):
        if status == 0:
            LOG.debug(i)
        else:
            LOG.error(i)
    return status


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
    if do_cmd(cmd) != 0:
        raise RuntimeError('failed to initialize the mon data directory!')

    # 启动服务
    LOG.debug('start monitor service')
    cmd = 'service ceph -c /etc/ceph/ceph.conf start mon.a'
    if do_cmd(cmd) != 0:
        raise RuntimeError('failed to start ceph monitor!')

    # 如果 mon data 是自己设置的, 不是使用默认值, 那么使用一下命令手动获取
    # client.admin keyring:
    # ceph auth --name=mon. --keyring=/var/lib/ceph/mon/ceph-a/keyring \
    # get-or-create client.admin mon 'allow *' osd 'allow *' mds 'allow *'


def install(args):
    pkg_install(args)
    gen_config(args)
    mon_install(args)


def mon_clean(args):
    # 先结束 ceph 服务的运行
    do_cmd('service ceph -c /etc/ceph/ceph.conf stop mon.a')

    # 删除 mon data
    if os.path.exists(mon_data):
        LOG.debug('delete mon data: %s', mon_data)
        shutil.rmtree(mon_data)
    else:
        LOG.warn('mon data %s not exists', mon_data)

    # 删除配置文件和 client.admin keyring
    if os.path.exists('/etc/ceph/ceph.conf'):
        os.remove('/etc/ceph/ceph.conf')
    if os.path.exists('/etc/ceph/ceph.client.admin.keyring'):
        os.remove('/etc/ceph/ceph.client.admin.keyring')


def clean(args):
    mon_clean(args)


def create_parser():
    parser = argparse.ArgumentParser(
        prog='ceph-aio',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Deploy ceph all in one\n\n',
        )
    parser.add_argument(
        'subcommand',
        metavar='SUBCOMMAND',
        choices=[
            'install',
            'clean',
            ],
        help='install clean',
        )
    parser.add_argument(
        '-d', '--data',
        dest='mon_data',
        help='ceph data, default: /var/lib/ceph',
        )
    return parser


def set_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(name)s] [%(levelname)s] %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


@exc.catches((KeyboardInterrupt, RuntimeError, exc.GToolsError,))
def main():
    parser = create_parser()
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit()
    else:
        args = parser.parse_args()

    set_logger()

    if args.subcommand == 'install':
        install(args)
    elif args.subcommand == 'clean':
        clean(args)
