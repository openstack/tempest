# Copyright 2016 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import inspect
import re
import time

from oslo_log import log as logging

from tempest.lib import exceptions

LOG = logging.getLogger(__name__)


def find_test_caller():
    """Find the caller class and test name.

    Because we know that the interesting things that call us are
    test_* methods, and various kinds of setUp / tearDown, we
    can look through the call stack to find appropriate methods,
    and the class we were in when those were called.
    """
    caller_name = None
    names = []
    frame = inspect.currentframe()
    is_cleanup = False
    # Start climbing the ladder until we hit a good method
    while True:
        try:
            frame = frame.f_back
            name = frame.f_code.co_name
            names.append(name)
            if re.search("^(test_|setUp|tearDown)", name):
                cname = ""
                if 'self' in frame.f_locals:
                    cname = frame.f_locals['self'].__class__.__name__
                if 'cls' in frame.f_locals:
                    cname = frame.f_locals['cls'].__name__
                caller_name = cname + ":" + name
                break
            elif re.search("^_run_cleanup", name):
                is_cleanup = True
            elif name == 'main':
                caller_name = 'main'
                break
            else:
                cname = ""
                if 'self' in frame.f_locals:
                    cname = frame.f_locals['self'].__class__.__name__
                if 'cls' in frame.f_locals:
                    cname = frame.f_locals['cls'].__name__

                # the fact that we are running cleanups is indicated pretty
                # deep in the stack, so if we see that we want to just
                # start looking for a real class name, and declare victory
                # once we do.
                if is_cleanup and cname:
                    if not re.search("^RunTest", cname):
                        caller_name = cname + ":_run_cleanups"
                        break
        except Exception:
            break
    # prevents frame leaks
    del frame
    if caller_name is None:
        LOG.debug("Sane call name not found in %s", names)
    return caller_name


def call_and_ignore_notfound_exc(func, *args, **kwargs):
    """Call the given function and pass if a `NotFound` exception is raised."""
    try:
        return func(*args, **kwargs)
    except exceptions.NotFound:
        pass


def call_until_true(func, duration, sleep_for, *args, **kwargs):
    """Call the given function until it returns True (and return True)

    or until the specified duration (in seconds) elapses (and return False).

    :param func: A callable that returns True on success.
    :param duration: The number of seconds for which to attempt a
        successful call of the function.
    :param sleep_for: The number of seconds to sleep after an unsuccessful
                      invocation of the function.
    :param args: args that are passed to func.
    :param kwargs: kwargs that are passed to func.
    """
    now = time.time()
    begin_time = now
    timeout = now + duration
    func_name = getattr(func, '__name__', getattr(func.__class__, '__name__'))
    while now < timeout:
        if func(*args, **kwargs):
            LOG.debug("Call %s returns true in %f seconds",
                      func_name, time.time() - begin_time)
            return True
        time.sleep(sleep_for)
        now = time.time()
    LOG.debug("Call %s returns false in %f seconds", func_name, duration)
    return False
