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
from tempest_lib import exceptions as lib_exc

from tempest.api.telemetry import base
from tempest import test


class TelemetryAlarmingAPITestJSON(base.BaseTelemetryTest):

    @classmethod
    def resource_setup(cls):
        super(TelemetryAlarmingAPITestJSON, cls).resource_setup()
        cls.rule = {'meter_name': 'cpu_util',
                    'comparison_operator': 'gt',
                    'threshold': 80.0,
                    'period': 70}
        for i in range(2):
            cls.create_alarm(threshold_rule=cls.rule)

    @test.attr(type="gate")
    @test.idempotent_id('1c918e06-210b-41eb-bd45-14676dd77cd6')
    def test_alarm_list(self):
        # List alarms
        alarm_list = self.telemetry_client.list_alarms()

        # Verify created alarm in the list
        fetched_ids = [a['alarm_id'] for a in alarm_list]
        missing_alarms = [a for a in self.alarm_ids if a not in fetched_ids]
        self.assertEqual(0, len(missing_alarms),
                         "Failed to find the following created alarm(s)"
                         " in a fetched list: %s" %
                         ', '.join(str(a) for a in missing_alarms))

    @test.attr(type="gate")
    @test.idempotent_id('1297b095-39c1-4e74-8a1f-4ae998cedd67')
    def test_create_update_get_delete_alarm(self):
        # Create an alarm
        alarm_name = data_utils.rand_name('telemetry_alarm')
        body = self.telemetry_client.create_alarm(
            name=alarm_name, type='threshold', threshold_rule=self.rule)
        self.assertEqual(alarm_name, body['name'])
        alarm_id = body['alarm_id']
        self.assertDictContainsSubset(self.rule, body['threshold_rule'])
        # Update alarm with new rule and new name
        new_rule = {'meter_name': 'cpu',
                    'comparison_operator': 'eq',
                    'threshold': 70.0,
                    'period': 60}
        alarm_name = data_utils.rand_name('telemetry-alarm-update')
        body = self.telemetry_client.update_alarm(
            alarm_id,
            threshold_rule=new_rule,
            name=alarm_name,
            type='threshold')
        self.assertEqual(alarm_name, body['name'])
        self.assertDictContainsSubset(new_rule, body['threshold_rule'])
        # Get and verify details of an alarm after update
        body = self.telemetry_client.get_alarm(alarm_id)
        self.assertEqual(alarm_name, body['name'])
        self.assertDictContainsSubset(new_rule, body['threshold_rule'])
        # Delete alarm and verify if deleted
        self.telemetry_client.delete_alarm(alarm_id)
        self.assertRaises(lib_exc.NotFound,
                          self.telemetry_client.get_alarm, alarm_id)

    @test.attr(type="gate")
    @test.idempotent_id('aca49486-70bb-4016-87e0-f6131374f741')
    def test_set_get_alarm_state(self):
        alarm_states = ['ok', 'alarm', 'insufficient data']
        alarm = self.create_alarm(threshold_rule=self.rule)
        # Set alarm state and verify
        new_state =\
            [elem for elem in alarm_states if elem != alarm['state']][0]
        state = self.telemetry_client.alarm_set_state(alarm['alarm_id'],
                                                      new_state)
        self.assertEqual(new_state, state.data)
        # Get alarm state and verify
        state = self.telemetry_client.alarm_get_state(alarm['alarm_id'])
        self.assertEqual(new_state, state.data)

    @test.attr(type="gate")
    @test.idempotent_id('08d7e45a-1344-4e5c-ba6f-f6cbb77f55b9')
    def test_create_delete_alarm_with_combination_rule(self):
        rule = {"alarm_ids": self.alarm_ids,
                "operator": "or"}
        # Verifies alarm create
        alarm_name = data_utils.rand_name('combination_alarm')
        body = self.telemetry_client.create_alarm(name=alarm_name,
                                                  combination_rule=rule,
                                                  type='combination')
        self.assertEqual(alarm_name, body['name'])
        alarm_id = body['alarm_id']
        self.assertDictContainsSubset(rule, body['combination_rule'])
        # Verify alarm delete
        self.telemetry_client.delete_alarm(alarm_id)
        self.assertRaises(lib_exc.NotFound,
                          self.telemetry_client.get_alarm, alarm_id)
