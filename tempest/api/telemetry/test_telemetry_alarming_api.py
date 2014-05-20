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

from tempest.api.telemetry import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest import test


class TelemetryAlarmingAPITestJSON(base.BaseTelemetryTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(TelemetryAlarmingAPITestJSON, cls).setUpClass()
        cls.rule = {'meter_name': 'cpu_util',
                    'comparison_operator': 'gt',
                    'threshold': 80.0,
                    'period': 70}
        for i in range(2):
            cls.create_alarm(threshold_rule=cls.rule)

    @test.attr(type="gate")
    def test_alarm_list(self):
        # List alarms
        resp, alarm_list = self.telemetry_client.list_alarms()
        self.assertEqual(200, resp.status)

        # Verify created alarm in the list
        fetched_ids = [a['alarm_id'] for a in alarm_list]
        missing_alarms = [a for a in self.alarm_ids if a not in fetched_ids]
        self.assertEqual(0, len(missing_alarms),
                         "Failed to find the following created alarm(s)"
                         " in a fetched list: %s" %
                         ', '.join(str(a) for a in missing_alarms))

    @test.attr(type="gate")
    def test_create_update_get_delete_alarm(self):
        # Create an alarm
        alarm_name = data_utils.rand_name('telemetry_alarm')
        resp, body = self.telemetry_client.create_alarm(
            name=alarm_name, type='threshold', threshold_rule=self.rule)
        self.assertEqual(201, resp.status)
        self.assertEqual(alarm_name, body['name'])
        alarm_id = body['alarm_id']
        self.assertDictContainsSubset(self.rule, body['threshold_rule'])
        # Update alarm with new rule and new name
        new_rule = {'meter_name': 'cpu',
                    'comparison_operator': 'eq',
                    'threshold': 70.0,
                    'period': 60}
        alarm_name = data_utils.rand_name('telemetry-alarm-update')
        resp, body = self.telemetry_client.update_alarm(
            alarm_id,
            threshold_rule=new_rule,
            name=alarm_name,
            type='threshold')
        self.assertEqual(200, resp.status)
        self.assertEqual(alarm_name, body['name'])
        self.assertDictContainsSubset(new_rule, body['threshold_rule'])
        # Get and verify details of an alarm after update
        resp, body = self.telemetry_client.get_alarm(alarm_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(alarm_name, body['name'])
        self.assertDictContainsSubset(new_rule, body['threshold_rule'])
        # Delete alarm and verify if deleted
        resp, _ = self.telemetry_client.delete_alarm(alarm_id)
        self.assertEqual(204, resp.status)
        self.assertRaises(exceptions.NotFound,
                          self.telemetry_client.get_alarm, alarm_id)

    @test.attr(type="gate")
    def test_set_get_alarm_state(self):
        alarm_states = ['ok', 'alarm', 'insufficient data']
        _, alarm = self.create_alarm(threshold_rule=self.rule)
        # Set alarm state and verify
        new_state =\
            [elem for elem in alarm_states if elem != alarm['state']][0]
        resp, state = self.telemetry_client.alarm_set_state(alarm['alarm_id'],
                                                            new_state)
        self.assertEqual(200, resp.status)
        self.assertEqual(new_state, state)
        # Get alarm state and verify
        resp, state = self.telemetry_client.alarm_get_state(alarm['alarm_id'])
        self.assertEqual(200, resp.status)
        self.assertEqual(new_state, state)

    @test.attr(type="gate")
    def test_create_delete_alarm_with_combination_rule(self):
        rule = {"alarm_ids": self.alarm_ids,
                "operator": "or"}
        # Verifies alarm create
        alarm_name = data_utils.rand_name('combination_alarm')
        resp, body = self.telemetry_client.create_alarm(name=alarm_name,
                                                        combination_rule=rule,
                                                        type='combination')
        self.assertEqual(201, resp.status)
        self.assertEqual(alarm_name, body['name'])
        alarm_id = body['alarm_id']
        self.assertDictContainsSubset(rule, body['combination_rule'])
        # Verify alarm delete
        resp, _ = self.telemetry_client.delete_alarm(alarm_id)
        self.assertEqual(204, resp.status)
        self.assertRaises(exceptions.NotFound,
                          self.telemetry_client.get_alarm, alarm_id)
