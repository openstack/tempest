# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import logging

from tempest.api.orchestration import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest.test import attr


LOG = logging.getLogger(__name__)


class TestServerStackLimits(base.BaseOrchestrationTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(TestServerStackLimits, cls).setUpClass()
        cls.client = cls.orchestration_client
        cls.stack_name = data_utils.rand_name('heat')

    @attr(type='gate')
    def test_exceed_max_template_size_fails(self):
        fill = 'A' * self.orchestration_cfg.max_template_size
        template = '''
HeatTemplateFormatVersion: '2012-12-12'
Description: '%s'
Outputs:
  Foo: bar''' % fill
        ex = self.assertRaises(exceptions.BadRequest, self.create_stack,
                               self.stack_name, template)
        self.assertIn('Template exceeds maximum allowed size', str(ex))
