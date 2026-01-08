# Copyright 2025 Red Hat, Inc.
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

from tempest.common import concurrency
from tempest.tests import base


class TestConcurrency(base.TestCase):

    def test_run_concurrent_tasks_success(self):
        """Test successful concurrent task execution."""
        def target_func(index, resource_ids, prefix='resource'):
            resource_ids.append(f"{prefix}_{index}")

        result = concurrency.run_concurrent_tasks(
            target_func,
            resource_count=3,
            prefix='test_resource'
        )

        self.assertEqual(len(result), 3)
        self.assertIn('test_resource_0', result)
        self.assertIn('test_resource_1', result)
        self.assertIn('test_resource_2', result)

    def test_run_concurrent_tasks_multiple_workers(self):
        """Test concurrent task execution with multiple workers."""
        def target_func(index, resource_ids):
            resource_ids.append(f"item_{index}")

        result = concurrency.run_concurrent_tasks(
            target_func,
            resource_count=4
        )

        self.assertEqual(len(result), 4)
        self.assertIn('item_0', result)
        self.assertIn('item_1', result)
        self.assertIn('item_2', result)
        self.assertIn('item_3', result)

    def test_run_concurrent_tasks_single_process(self):
        """Test concurrent task execution with single process."""
        def target_func(index, resource_ids, value):
            resource_ids.append(value * 2)

        result = concurrency.run_concurrent_tasks(
            target_func,
            resource_count=1,
            value=5
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 10)

    def test_run_concurrent_tasks_with_exception(self):
        """Test that exceptions in tasks are properly captured and raised."""
        def failing_target(index, resource_ids):
            if index == 1:
                raise ValueError("Test error in worker 1")
            resource_ids.append(f"resource_{index}")

        error = self.assertRaises(
            RuntimeError,
            concurrency.run_concurrent_tasks,
            failing_target,
            resource_count=3
        )
        self.assertIn("Worker 1 failed", str(error))
        self.assertIn("Test error in worker 1", str(error))

    def test_run_concurrent_tasks_dict_return_values(self):
        """Test concurrent task execution with dict return values."""
        def target_returning_dict(index, resource_ids):
            resource_ids.append({'id': index, 'name': f'resource_{index}'})

        result = concurrency.run_concurrent_tasks(
            target_returning_dict,
            resource_count=3
        )

        self.assertEqual(len(result), 3)
        # Verify that dicts are present
        ids = [r['id'] for r in result]
        self.assertIn(0, ids)
        self.assertIn(1, ids)
        self.assertIn(2, ids)
