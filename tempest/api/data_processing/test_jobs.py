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

from tempest.api.data_processing import base as dp_base
from tempest.common.utils import data_utils
from tempest import test


class JobTest(dp_base.BaseDataProcessingTest):
    """Link to the API documentation is http://docs.openstack.org/developer/
    sahara/restapi/rest_api_v1.1_EDP.html#jobs
    """
    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(JobTest, cls).setUpClass()
        # create job binary
        job_binary = {
            'name': data_utils.rand_name('sahara-job-binary'),
            'url': 'swift://sahara-container.sahara/example.jar',
            'description': 'Test job binary',
            'extra': {
                'user': cls.os.credentials.username,
                'password': cls.os.credentials.password
            }
        }
        resp_body = cls.create_job_binary(**job_binary)
        job_binary_id = resp_body['id']

        cls.job = {
            'job_type': 'Pig',
            'mains': [job_binary_id]
        }

    def _create_job(self, job_name=None):
        """Creates Job with optional name specified.

        It creates job and ensures job name. Returns id and name of created
        job.
        """
        if not job_name:
            # generate random name if it's not specified
            job_name = data_utils.rand_name('sahara-job')

        # create job
        resp_body = self.create_job(job_name, **self.job)

        # ensure that job created successfully
        self.assertEqual(job_name, resp_body['name'])

        return resp_body['id'], job_name

    @test.attr(type='smoke')
    def test_job_create(self):
        self._create_job()

    @test.attr(type='smoke')
    def test_job_list(self):
        job_info = self._create_job()

        # check for job in list
        _, jobs = self.client.list_jobs()
        jobs_info = [(job['id'], job['name']) for job in jobs]
        self.assertIn(job_info, jobs_info)

    @test.attr(type='smoke')
    def test_job_get(self):
        job_id, job_name = self._create_job()

        # check job fetch by id
        _, job = self.client.get_job(job_id)
        self.assertEqual(job_name, job['name'])

    @test.attr(type='smoke')
    def test_job_delete(self):
        job_id, _ = self._create_job()

        # delete the job by id
        self.client.delete_job(job_id)
