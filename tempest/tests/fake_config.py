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
        cfg.CONF([], default_config_files=[])
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
        lock_path = str(os.environ.get('OS_TEST_LOCK_PATH',
                                       os.environ.get('TMPDIR', '/tmp')))
        if not os.path.exists(lock_path):
            os.mkdir(lock_path)
        lockutils.set_defaults(
            lock_path=lock_path,
        )
        self.conf.set_default('auth_version', 'v2', group='identity')
        for config_option in ['username', 'password', 'project_name']:
            # Identity group items
            self.conf.set_default('admin_' + config_option,
                                  'fake_' + config_option,
                                  group='auth')


class FakePrivate(config.TempestConfigPrivate):
    def __init__(self, parse_conf=True, config_path=None):
        self._set_attrs()
        self.lock_path = cfg.CONF.oslo_concurrency.lock_path

fake_service1_group = cfg.OptGroup(name='fake-service1', title='Fake service1')

FakeService1Group = [
    cfg.StrOpt('catalog_type', default='fake-service1'),
    cfg.StrOpt('endpoint_type', default='faketype'),
    cfg.StrOpt('region', default='fake_region'),
    cfg.IntOpt('build_timeout', default=99),
    cfg.IntOpt('build_interval', default=9)]

fake_service2_group = cfg.OptGroup(name='fake-service2', title='Fake service2')

FakeService2Group = [
    cfg.StrOpt('catalog_type', default='fake-service2'),
    cfg.StrOpt('endpoint_type', default='faketype')]


class ServiceClientsConfigFixture(conf_fixture.Config):

    def __init__(self):
        cfg.CONF([], default_config_files=[])
        config._opts.append((fake_service1_group, FakeService1Group))
        config._opts.append((fake_service2_group, FakeService2Group))
        config.register_opts()
        super(ServiceClientsConfigFixture, self).__init__()

    def setUp(self):
        super(ServiceClientsConfigFixture, self).setUp()
        # Debug default values
        self.conf.set_default('trace_requests', 'fake_module', 'debug')
        # Identity default values
        self.conf.set_default('disable_ssl_certificate_validation', True,
                              group='identity')
        self.conf.set_default('ca_certificates_file', '/fake/certificates',
                              group='identity')
        self.conf.set_default('region', 'fake_region', 'identity')
        # Compute default values
        self.conf.set_default('build_interval', 88, group='compute')
        self.conf.set_default('build_timeout', 8, group='compute')


class ServiceClientsFakePrivate(config.TempestConfigPrivate):
    def __init__(self, parse_conf=True, config_path=None):
        self._set_attrs()
        self.fake_service1 = cfg.CONF['fake-service1']
        self.fake_service2 = cfg.CONF['fake-service2']
        self.lock_path = cfg.CONF.oslo_concurrency.lock_path
