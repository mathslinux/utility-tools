#encoding: utf-8

import logging
import os
import shutil
import uuid
from utils import ceph_data, osd_data, do_cmd

LOG = logging.getLogger('ceph-aio')


def osd_install(args):
    """创建并启动 osd data 然后启动
    分为三步:
    1. 用 ceph osd create [uuid] 创建 osd
    2. 用 ceph-osd 初始化 osd data
    3. 创建 osd 的认证信息

    这里, 我创建4个 osd 服务.
    """
    for i in range(4):
        data = os.path.join(osd_data, 'ceph-%d' % (i))

        # 准备 osd data
        LOG.debug('create osd data: %s', data)
        if os.path.exists(data):
            LOG.warn('osd data exists, delete it')
            shutil.rmtree(data)
        os.makedirs(data, mode=0700)

        # 创建 osd
        LOG.debug('create osd')
        ret, out = do_cmd('ceph osd create %s' % (str(uuid.uuid4())))
        if ret != 0:
            raise RuntimeError('failed to create osd: %s' % (out))
        osd_id = out
        LOG.debug('osd.%s is created', osd_id)

        # 初始化 osd data
        LOG.debug('inital osd data')
        do_cmd('ceph mon getmap -o /tmp/ceph.mon')
        cmd = ('ceph-osd -i {osd_id} --mkfs --mkkey --monmap {monmap} '
               '--osd-data {osd_data} --osd-journal {journal} '
               '--osd-uuid {osd_uuid} --keyring {keyring}'.format(
                   osd_id=osd_id,
                   monmap='/tmp/ceph.mon',
                   osd_data=data,
                   journal=os.path.join(data, 'journal'),
                   osd_uuid=str(uuid.uuid4()),
                   keyring=os.path.join(data, 'keyring')
               ))
        ret, out = do_cmd(cmd)
        if ret != 0:
            raise RuntimeError('failed to initial osd.%s' % (osd_id))

        # 创建 osd 的认证信息
        cmd = ("ceph --name client.bootstrap-osd --keyring {boot_keyring} "
               "auth add osd.{osd_id} -i {keyring} "
               "osd 'allow *' mon 'allow profile osd'".format(
                   boot_keyring=os.path.join(ceph_data, 'bootstrap-osd/ceph.keyring'),
                   osd_id=osd_id,
                   keyring=os.path.join(data, 'keyring')
               ))
        ret, out = do_cmd(cmd)
        if ret != 0:
            LOG.warn('failed to register osd auth: %s', out)

        # 为 sysvinit 的service 创建服务
        do_cmd('touch %s' % (os.path.join(data, 'sysvinit')))

        # 启动服务
        do_cmd('service ceph start osd.{osd_id}'.format(osd_id=osd_id))


def osd_clean(args):
    # 根据 ceph 的官方文档, 删除 osd 需要以下步奏:
    # 1) 把 待删除的 osd 标记为 out:    ceph ceph osd out {osd_id}
    # 2) 结束 ceph osd 的运行:        service ceph stop osd.{osd_id}
    # 3) 把 osd 从 crush 里面删除:    ceph osd crush remove osd.0
    # 4) 删除 osd 的认证信息:         ceph auth del osd.0
    # 5) 删除 osd:                 ceph osd rm 0
    LOG.debug('clean ceph osd')
    for osd_id in range(4):
        do_cmd('ceph osd out {id}'.format(id=osd_id))
        do_cmd('service ceph stop osd.{id}'.format(id=osd_id))
        do_cmd('ceph osd crush remove osd.{id}'.format(id=osd_id))
        do_cmd('ceph auth del osd.{id}'.format(id=osd_id))
        do_cmd('ceph osd rm {id}'.format(id=osd_id))

        # 删除 mon data
        data = os.path.join(osd_data, 'ceph-{id}'.format(id=osd_id))
        if os.path.exists(data):
            LOG.debug('delete mon data: %s', data)
            shutil.rmtree(data)
        else:
            LOG.warn('osd data %s not exists', data)
