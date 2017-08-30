# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.

from __future__ import print_function
import threading
import gevent
import gevent.monkey
import gevent.local
import gevent.pool
from functools import wraps
import logging

logger = logging.getLogger(__name__)
enabled = False

pool = gevent.pool.Pool(200)
spawn = pool.spawn
joinall = gevent.joinall


sleep = gevent.sleep


def enable_async():
    global enabled

    if enabled:
        return enabled

    if threading.active_count() > 3:
        # This number used to be 1, but a gevent patch or something else changed this so it starts with 3 threads
        logger.warning('{} threads already running. gvent monkey patching disabled...'.format(threading.active_count()))
        enabled = False

    else:
        logger.debug('Monkey patching using gevent')
        gevent.monkey.patch_all()
        enabled = True

    return enabled


def join_routines(routines):
    greenlets = [_ for _ in routines if isinstance(_, gevent.Greenlet)]
    if enabled:
        gevent.joinall(greenlets)


def async_routine(f):
    @wraps(f)
    def to_list(*args, **kwargs):
        output = f(*args, **kwargs)
        if output is not None:
            return list(output)

    def async_wrapped_routine(*args, **kwargs):
        run_async = kwargs.pop('async', True)
        if enabled and run_async:
            logger.debug('Spawning greenlet to run {}({}) asynchronously'.format(f.func_name, args))
            return spawn(to_list, *args, **kwargs)
        else:
            logger.debug('Asynchronous support disabled. Running {}({}) in a thread'.format(f.func_name, args))
            to_list(*args, **kwargs)
    return async_wrapped_routine
