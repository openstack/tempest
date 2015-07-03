# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


from tempest.api.object_storage import base
from tempest.common import custom_matchers
from tempest import test
from tempest_lib import decorators


class HealthcheckTest(base.BaseObjectTest):

    def setUp(self):
        super(HealthcheckTest, self).setUp()
        # Turning http://.../v1/foobar into http://.../
        self.account_client.skip_path()

    @decorators.skip_because(bug="1", reason='healthcheck file does not '
                                'exist in ceph server.')
    @test.attr('gate')
    @test.idempotent_id('db5723b1-f25c-49a9-bfeb-7b5640caf337')
    def test_get_healthcheck(self):

        resp, _ = self.account_client.get("healthcheck", {})

        # The target of the request is not any Swift resource. Therefore, the
        # existence of response header is checked without a custom matcher.
        self.assertIn('content-length', resp)
        self.assertIn('content-type', resp)
        self.assertIn('x-trans-id', resp)
        self.assertIn('date', resp)
        # Check only the format of common headers with custom matcher
        self.assertThat(resp, custom_matchers.AreAllWellFormatted())
