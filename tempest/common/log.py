# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 NEC Corporation.
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

import ConfigParser
import inspect
import logging
import logging.config
import os
import re

from oslo.config import cfg


_DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)8s [%(name)s] %(message)s"
_DEFAULT_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_loggers = {}


def getLogger(name='unknown'):
    if len(_loggers) == 0:
        loaded = _load_log_config()
        getLogger.adapter = TestsAdapter if loaded else None

    if name not in _loggers:
        logger = logging.getLogger(name)
        if getLogger.adapter:
            _loggers[name] = getLogger.adapter(logger, name)
        else:
            _loggers[name] = logger

    return _loggers[name]


def _load_log_config():
    conf_dir = os.environ.get('TEMPEST_LOG_CONFIG_DIR', None)
    conf_file = os.environ.get('TEMPEST_LOG_CONFIG', None)
    if not conf_dir or not conf_file:
        return False

    log_config = os.path.join(conf_dir, conf_file)
    try:
        logging.config.fileConfig(log_config)
    except ConfigParser.Error, exc:
        raise cfg.ConfigFileParseError(log_config, str(exc))
    return True


class TestsAdapter(logging.LoggerAdapter):

    def __init__(self, logger, project_name):
        self.logger = logger
        self.project = project_name
        self.regexp = re.compile(r"test_\w+\.py")

    def __getattr__(self, key):
        return getattr(self.logger, key)

    def _get_test_name(self):
        frames = inspect.stack()
        for frame in frames:
            binary_name = frame[1]
            if self.regexp.search(binary_name) and 'self' in frame[0].f_locals:
                return frame[0].f_locals.get('self').id()
            elif frame[3] == '_run_cleanups':
                #NOTE(myamazaki): method calling addCleanup
                return frame[0].f_locals.get('self').case.id()
            elif frame[3] in ['setUpClass', 'tearDownClass']:
                #NOTE(myamazaki): setUpClass or tearDownClass
                return "%s.%s.%s" % (frame[0].f_locals['cls'].__module__,
                                     frame[0].f_locals['cls'].__name__,
                                     frame[3])
        return None

    def process(self, msg, kwargs):
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        extra = kwargs['extra']

        test_name = self._get_test_name()
        if test_name:
            extra.update({'testname': test_name})
        extra['extra'] = extra.copy()

        return msg, kwargs


class TestsFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None):
        super(TestsFormatter, self).__init__()
        self.default_format = _DEFAULT_LOG_FORMAT
        self.testname_format =\
            "%(asctime)s %(levelname)8s [%(testname)s] %(message)s"
        self.datefmt = _DEFAULT_LOG_DATE_FORMAT

    def format(self, record):
        extra = record.__dict__.get('extra', None)
        if extra and 'testname' in extra:
            self._fmt = self.testname_format
        else:
            self._fmt = self.default_format
        return logging.Formatter.format(self, record)
