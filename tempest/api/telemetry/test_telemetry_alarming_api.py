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
from tempest import exceptions
from tempest.test import attr


class TelemetryAlarmingAPITestJSON(base.BaseTelemetryTest):
    _interface = 'json'

    @attr(type="gate")
    def test_alarm_list(self):
        resp, _ = self.telemetry_client.list_alarms()
        self.assertEqual(int(resp['status']), 200)

    @attr(type="gate")
    def test_create_alarm(self):
        rules = {'meter_name': 'cpu_util',
                 'comparison_operator': 'gt',
                 'threshold': 80.0,
                 'period': 70}
        resp, body = self.create_alarm(threshold_rule=rules)
        self.alarm_id = body['alarm_id']
        self.assertEqual(int(resp['status']), 201)
        self.assertDictContainsSubset(rules, body['threshold_rule'])
        resp, body = self.telemetry_client.get_alarm(self.alarm_id)
        self.assertEqual(int(resp['status']), 200)
        self.assertDictContainsSubset(rules, body['threshold_rule'])
        resp, _ = self.telemetry_client.delete_alarm(self.alarm_id)
        self.assertEqual(int(resp['status']), 204)
        self.assertRaises(exceptions.NotFound,
                          self.telemetry_client.get_alarm,
                          self.alarm_id)
