#encoding: utf-8

import os
import commands
import logging

# TODO: let user decides ceph_data
# TODO: 解释为什么 ceph_data 一定要是这个
ceph_data = '/var/lib/ceph'
mon_data = os.path.join(ceph_data, 'mon/ceph-a')
osd_data = os.path.join(ceph_data, 'osd')

LOG = logging.getLogger('ceph-aio')


def do_cmd(cmd):
    LOG.debug('execute command: "%s"', cmd)
    (status, out) = commands.getstatusoutput(cmd)
    for i in out.split('\n'):
        if status == 0:
            LOG.debug(i)
        else:
            LOG.error(i)
    return status, out
