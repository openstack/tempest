# Copyright (c) 2014 Mirantis Inc.
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

from tempest_lib.common.utils import data_utils

from tempest.api.data_processing import base as dp_base
from tempest import test


class JobBinaryInternalTest(dp_base.BaseDataProcessingTest):
    """Link to the API documentation is http://docs.openstack.org/developer/
    sahara/restapi/rest_api_v1.1_EDP.html#job-binary-internals
    """
    @classmethod
    def resource_setup(cls):
        super(JobBinaryInternalTest, cls).resource_setup()
        cls.job_binary_internal_data = 'Some script may be data'

    def _create_job_binary_internal(self, binary_name=None):
        """Creates Job Binary Internal with optional name specified.

        It puts data into Sahara database and ensures job binary internal name.
        Returns id and name of created job binary internal.
        """
        if not binary_name:
            # generate random name if it's not specified
            binary_name = data_utils.rand_name('sahara-job-binary-internal')

        # create job binary internal
        resp_body = (
            self.create_job_binary_internal(binary_name,
                                            self.job_binary_internal_data))

        # ensure that job binary internal created successfully
        self.assertEqual(binary_name, resp_body['name'])

        return resp_body['id'], binary_name

    @test.attr(type='smoke')
    @test.idempotent_id('249c4dc2-946f-4939-83e6-212ddb6ea0be')
    def test_job_binary_internal_create(self):
        self._create_job_binary_internal()

    @test.attr(type='smoke')
    @test.idempotent_id('1e3c2ecd-5673-499d-babe-4fe2fcdf64ee')
    def test_job_binary_internal_list(self):
        binary_info = self._create_job_binary_internal()

        # check for job binary internal in list
        binaries = self.client.list_job_binary_internals()
        binaries_info = [(binary['id'], binary['name']) for binary in binaries]
        self.assertIn(binary_info, binaries_info)

    @test.attr(type='smoke')
    @test.idempotent_id('a2046a53-386c-43ab-be35-df54b19db776')
    def test_job_binary_internal_get(self):
        binary_id, binary_name = self._create_job_binary_internal()

        # check job binary internal fetch by id
        binary = self.client.get_job_binary_internal(binary_id)
        self.assertEqual(binary_name, binary['name'])

    @test.attr(type='smoke')
    @test.idempotent_id('b3568c33-4eed-40d5-aae4-6ff3b2ac58f5')
    def test_job_binary_internal_delete(self):
        binary_id, _ = self._create_job_binary_internal()

        # delete the job binary internal by id
        self.client.delete_job_binary_internal(binary_id)

    @test.attr(type='smoke')
    @test.idempotent_id('8871f2b0-5782-4d66-9bb9-6f95bcb839ea')
    def test_job_binary_internal_get_data(self):
        binary_id, _ = self._create_job_binary_internal()

        # get data of job binary internal by id
        _, data = self.client.get_job_binary_internal_data(binary_id)
        self.assertEqual(data, self.job_binary_internal_data)
