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

from tempest_lib.common.utils import data_utils

from tempest.api.orchestration import base
from tempest import test


class TemplateYAMLTestJSON(base.BaseOrchestrationTest):
    template = """
HeatTemplateFormatVersion: '2012-12-12'
Description: |
  Template which creates only a new user
Resources:
  CfnUser:
    Type: AWS::IAM::User
"""

    @classmethod
    def resource_setup(cls):
        super(TemplateYAMLTestJSON, cls).resource_setup()
        cls.stack_name = data_utils.rand_name('heat')
        cls.stack_identifier = cls.create_stack(cls.stack_name, cls.template)
        cls.client.wait_for_stack_status(cls.stack_identifier,
                                         'CREATE_COMPLETE')
        cls.stack_id = cls.stack_identifier.split('/')[1]
        cls.parameters = {}

    @test.attr(type='gate')
    @test.idempotent_id('47430699-c368-495e-a1db-64c26fd967d7')
    def test_show_template(self):
        """Getting template used to create the stack."""
        self.client.show_template(self.stack_identifier)

    @test.attr(type='gate')
    @test.idempotent_id('ed53debe-8727-46c5-ab58-eba6090ec4de')
    def test_validate_template(self):
        """Validating template passing it content."""
        self.client.validate_template(self.template,
                                      self.parameters)


class TemplateAWSTestJSON(TemplateYAMLTestJSON):
    template = """
{
  "AWSTemplateFormatVersion" : "2010-09-09",
  "Description" : "Template which creates only a new user",
  "Resources" : {
    "CfnUser" : {
      "Type" : "AWS::IAM::User"
    }
  }
}
"""
