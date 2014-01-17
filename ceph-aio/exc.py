import logging
from functools import wraps
import sys


class GToolsError(Exception):
    """
    Unknown gtools error
    """

    def __str__(self):
        doc = self.__doc__.strip()
        return ': '.join([doc] + [str(a) for a in self.args])


class ArgumentError(Exception):
    """Argument error"""


class OpenError(Exception):
    """Open error"""


def catches(catch=None, handler=None, exit=True):
    catch = catch or Exception
    logger = logging.getLogger('ceph-aio')

    def decorate(f):
        @wraps(f)
        def newfunc(*a, **kw):
            try:
                return f(*a, **kw)
            except catch as e:
                if handler:
                    return handler(e)
                else:
                    logger.error(make_exception_message(e))
                    if exit:
                        sys.exit(1)
        return newfunc

    return decorate


def make_exception_message(exc):
    """
    An exception is passed in and this function
    returns the proper string depending on the result
    so it is readable enough.
    """
    if str(exc):
        return '%s: %s\n' % (exc.__class__.__name__, exc)
    else:
        return '%s\n' % (exc.__class__.__name__)
