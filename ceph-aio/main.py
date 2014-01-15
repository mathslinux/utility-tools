"""
ceph-aio: deploy ceph all in one
usage:
  ceph-aio install
  ceph-aio clean
  ceph-aio -h
"""

import sys
import argparse


def install(args):
    pass


def clean(args):
    pass


def create_parser():
    parser = argparse.ArgumentParser(
        prog='ceph-aio',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Deploy ceph all in one\n\n',
        )
    sub = parser.add_subparsers(
        title='Commands',
        metavar='COMMAND',
        help='description',
        )

    # install command
    p = sub.add_parser(
        'install',
        help='install ceph all in box'
    )
    p.set_defaults(func=install)

    # clean command
    p = sub.add_parser(
        'clean',
        help='clean ceph install by ceph-aio'
    )
    p.set_defaults(func=clean)

    return parser


def main():
    parser = create_parser()
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit()
    else:
        args = parser.parse_args()

    return args.func(args)
