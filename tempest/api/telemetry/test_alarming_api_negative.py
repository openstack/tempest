#    Copyright 2015 GlobalLogic.  All rights reserved.
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

from tempest.api.telemetry import base
from tempest.common.utils import data_utils
from tempest.lib import exceptions as lib_exc
from tempest import test


class TelemetryAlarmingNegativeTest(base.BaseAlarmingTest):
    """Negative tests for show_alarm, update_alarm, show_alarm_history tests

        ** show non-existent alarm
        ** show the deleted alarm
        ** delete deleted alarm
        ** update deleted alarm
    """

    @test.attr(type=['negative'])
    @test.idempotent_id('668743d5-08ad-4480-b2b8-15da34f81e7d')
    def test_get_non_existent_alarm(self):
        # get the non-existent alarm
        non_existent_id = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound, self.alarming_client.show_alarm,
                          non_existent_id)

    @test.attr(type=['negative'])
    @test.idempotent_id('ef45000d-0a72-4781-866d-4cb7bf2582ad')
    def test_get_update_show_history_delete_deleted_alarm(self):
        # get, update and delete the deleted alarm
        alarm_name = data_utils.rand_name('telemetry_alarm')
        rule = {'meter_name': 'cpu',
                'comparison_operator': 'eq',
                'threshold': 100.0,
                'period': 90}
        body = self.alarming_client.create_alarm(
            name=alarm_name,
            type='threshold',
            threshold_rule=rule)
        alarm_id = body['alarm_id']
        self.alarming_client.delete_alarm(alarm_id)
        # get the deleted alarm
        self.assertRaises(lib_exc.NotFound, self.alarming_client.show_alarm,
                          alarm_id)

        # update the deleted alarm
        updated_alarm_name = data_utils.rand_name('telemetry_alarm_updated')
        updated_rule = {'meter_name': 'cpu_new',
                        'comparison_operator': 'eq',
                        'threshold': 70,
                        'period': 50}
        self.assertRaises(lib_exc.NotFound, self.alarming_client.update_alarm,
                          alarm_id, threshold_rule=updated_rule,
                          name=updated_alarm_name,
                          type='threshold')
        # delete the deleted alarm
        self.assertRaises(lib_exc.NotFound, self.alarming_client.delete_alarm,
                          alarm_id)
