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

from tempest.api.orchestration import base
from tempest.common.utils import data_utils
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
    @test.safe_setup
    def setUpClass(cls):
        super(TemplateYAMLTestJSON, cls).setUpClass()
        cls.stack_name = data_utils.rand_name('heat')
        cls.stack_identifier = cls.create_stack(cls.stack_name, cls.template)
        cls.client.wait_for_stack_status(cls.stack_identifier,
                                         'CREATE_COMPLETE')
        cls.stack_id = cls.stack_identifier.split('/')[1]
        cls.parameters = {}

    @test.attr(type='gate')
    def test_show_template(self):
        """Getting template used to create the stack."""
        _, template = self.client.show_template(self.stack_identifier)

    @test.attr(type='gate')
    def test_validate_template(self):
        """Validating template passing it content."""
        _, parameters = self.client.validate_template(self.template,
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
