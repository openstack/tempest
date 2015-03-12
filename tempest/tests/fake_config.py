# Copyright 2013 IBM Corp.
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

import os

from oslo_concurrency import lockutils
from oslo_config import cfg
from oslo_config import fixture as conf_fixture

from tempest import config


class ConfigFixture(conf_fixture.Config):

    def __init__(self):
        config.register_opts()
        super(ConfigFixture, self).__init__()

    def setUp(self):
        super(ConfigFixture, self).setUp()
        self.conf.set_default('build_interval', 10, group='compute')
        self.conf.set_default('build_timeout', 10, group='compute')
        self.conf.set_default('disable_ssl_certificate_validation', True,
                              group='identity')
        self.conf.set_default('uri', 'http://fake_uri.com/auth',
                              group='identity')
        self.conf.set_default('uri_v3', 'http://fake_uri_v3.com/auth',
                              group='identity')
        self.conf.set_default('neutron', True, group='service_available')
        self.conf.set_default('heat', True, group='service_available')
        if not os.path.exists(str(os.environ.get('OS_TEST_LOCK_PATH'))):
            os.mkdir(str(os.environ.get('OS_TEST_LOCK_PATH')))
        lockutils.set_defaults(
            lock_path=str(os.environ.get('OS_TEST_LOCK_PATH')),
        )
        self.conf.set_default('auth_version', 'v2', group='identity')
        for config_option in ['username', 'password', 'tenant_name']:
            # Identity group items
            for prefix in ['', 'alt_', 'admin_']:
                self.conf.set_default(prefix + config_option,
                                      'fake_' + config_option,
                                      group='identity')


class FakePrivate(config.TempestConfigPrivate):
    def __init__(self, parse_conf=True, config_path=None):
        cfg.CONF([], default_config_files=[])
        self._set_attrs()
        self.lock_path = cfg.CONF.lock_path
