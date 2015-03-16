# Copyright 2012 OpenStack Foundation
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

import re
import time

import boto.exception
from oslo_log import log as logging
import testtools

from tempest import config

CONF = config.CONF
LOG = logging.getLogger(__name__)


def state_wait(lfunction, final_set=set(), valid_set=None):
    # TODO(afazekas): evaluate using ABC here
    if not isinstance(final_set, set):
        final_set = set((final_set,))
    if not isinstance(valid_set, set) and valid_set is not None:
        valid_set = set((valid_set,))
    start_time = time.time()
    old_status = status = lfunction()
    while True:
        if status != old_status:
            LOG.info('State transition "%s" ==> "%s" %d second', old_status,
                     status, time.time() - start_time)
        if status in final_set:
            return status
        if valid_set is not None and status not in valid_set:
            return status
        dtime = time.time() - start_time
        if dtime > CONF.boto.build_timeout:
            raise testtools.TestCase\
                .failureException("State change timeout exceeded!"
                                  '(%ds) While waiting'
                                  'for %s at "%s"' %
                                  (dtime, final_set, status))
        time.sleep(CONF.boto.build_interval)
        old_status = status
        status = lfunction()


def re_search_wait(lfunction, regexp):
    """Stops waiting on success."""
    start_time = time.time()
    while True:
        text = lfunction()
        result = re.search(regexp, text)
        if result is not None:
            LOG.info('Pattern "%s" found in %d second in "%s"',
                     regexp,
                     time.time() - start_time,
                     text)
            return result
        dtime = time.time() - start_time
        if dtime > CONF.boto.build_timeout:
            raise testtools.TestCase\
                .failureException('Pattern find timeout exceeded!'
                                  '(%ds) While waiting for'
                                  '"%s" pattern in "%s"' %
                                  (dtime, regexp, text))
        time.sleep(CONF.boto.build_interval)


def wait_no_exception(lfunction, exc_class=None, exc_matcher=None):
    """Stops waiting on success."""
    start_time = time.time()
    if exc_matcher is not None:
        exc_class = boto.exception.BotoServerError

    if exc_class is None:
        exc_class = BaseException
    while True:
        result = None
        try:
            result = lfunction()
            LOG.info('No Exception in %d second',
                     time.time() - start_time)
            return result
        except exc_class as exc:
            if exc_matcher is not None:
                res = exc_matcher.match(exc)
                if res is not None:
                    LOG.info(res)
                    raise exc
        # Let the other exceptions propagate
        dtime = time.time() - start_time
        if dtime > CONF.boto.build_timeout:
            raise testtools.TestCase\
                .failureException("Wait timeout exceeded! (%ds)" % dtime)
        time.sleep(CONF.boto.build_interval)


# NOTE(afazekas): EC2/boto normally raise exception instead of empty list
def wait_exception(lfunction):
    """Returns with the exception or raises one."""
    start_time = time.time()
    while True:
        try:
            lfunction()
        except BaseException as exc:
            LOG.info('Exception in %d second',
                     time.time() - start_time)
            return exc
        dtime = time.time() - start_time
        if dtime > CONF.boto.build_timeout:
            raise testtools.TestCase\
                .failureException("Wait timeout exceeded! (%ds)" % dtime)
        time.sleep(CONF.boto.build_interval)

# TODO(afazekas): consider strategy design pattern..
