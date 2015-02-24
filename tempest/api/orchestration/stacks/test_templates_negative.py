# Copyright 2014 NEC Corporation.  All rights reserved.
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

from tempest_lib import exceptions as lib_exc

from tempest.api.orchestration import base
from tempest import test


class TemplateYAMLNegativeTestJSON(base.BaseOrchestrationTest):
    template = """
HeatTemplateFormatVersion: '2012-12-12'
Description: |
  Template which creates only a new user
Resources:
  CfnUser:
    Type: AWS::IAM::User
"""

    invalid_template_url = 'http://www.example.com/template.yaml'

    @classmethod
    def resource_setup(cls):
        super(TemplateYAMLNegativeTestJSON, cls).resource_setup()
        cls.parameters = {}

    @test.attr(type=['gate', 'negative'])
    @test.idempotent_id('5586cbca-ddc4-4152-9db8-fa1ce5fc1876')
    def test_validate_template_url(self):
        """Validating template passing url to it."""
        self.assertRaises(lib_exc.BadRequest,
                          self.client.validate_template_url,
                          template_url=self.invalid_template_url,
                          parameters=self.parameters)


class TemplateAWSNegativeTestJSON(TemplateYAMLNegativeTestJSON):
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

    invalid_template_url = 'http://www.example.com/template.template'
