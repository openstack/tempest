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

from tempest_lib.common.utils import data_utils as utils

from tempest.api.volume import base
from tempest import test


class QosSpecsV2TestJSON(base.BaseVolumeAdminTest):
    """Test the Cinder QoS-specs.

    Tests for  create, list, delete, show, associate,
    disassociate, set/unset key V2 APIs.
    """

    @classmethod
    def resource_setup(cls):
        super(QosSpecsV2TestJSON, cls).resource_setup()
        # Create admin qos client
        # Create a test shared qos-specs for tests
        cls.qos_name = utils.rand_name(cls.__name__ + '-QoS')
        cls.qos_consumer = 'front-end'

        cls.created_qos = cls.create_test_qos_specs(cls.qos_name,
                                                    cls.qos_consumer,
                                                    read_iops_sec='2000')

    def _create_delete_test_qos_with_given_consumer(self, consumer):
        name = utils.rand_name('qos')
        qos = {'name': name, 'consumer': consumer}
        body = self.create_test_qos_specs(name, consumer)
        for key in ['name', 'consumer']:
            self.assertEqual(qos[key], body[key])

        self.volume_qos_client.delete_qos(body['id'])
        self.volume_qos_client.wait_for_resource_deletion(body['id'])

        # validate the deletion
        list_qos = self.volume_qos_client.list_qos()
        self.assertNotIn(body, list_qos)

    def _create_test_volume_type(self):
        vol_type_name = utils.rand_name("volume-type")
        vol_type = self.volume_types_client.create_volume_type(
            vol_type_name)
        self.addCleanup(self.volume_types_client.delete_volume_type,
                        vol_type['id'])
        return vol_type

    def _test_associate_qos(self, vol_type_id):
        self.volume_qos_client.associate_qos(
            self.created_qos['id'], vol_type_id)

    def _test_get_association_qos(self):
        body = self.volume_qos_client.show_association_qos(
            self.created_qos['id'])

        associations = []
        for association in body:
            associations.append(association['id'])

        return associations

    @test.idempotent_id('7e15f883-4bef-49a9-95eb-f94209a1ced1')
    def test_create_delete_qos_with_front_end_consumer(self):
        """Tests the creation and deletion of QoS specs

        With consumer as front end
        """
        self._create_delete_test_qos_with_given_consumer('front-end')

    @test.idempotent_id('b115cded-8f58-4ee4-aab5-9192cfada08f')
    def test_create_delete_qos_with_back_end_consumer(self):
        """Tests the creation and deletion of QoS specs

        With consumer as back-end
        """
        self._create_delete_test_qos_with_given_consumer('back-end')

    @test.attr(type='smoke')
    @test.idempotent_id('f88d65eb-ea0d-487d-af8d-71f4011575a4')
    def test_create_delete_qos_with_both_consumer(self):
        """Tests the creation and deletion of QoS specs

        With consumer as both front end and back end
        """
        self._create_delete_test_qos_with_given_consumer('both')

    @test.attr(type='smoke')
    @test.idempotent_id('7aa214cc-ac1a-4397-931f-3bb2e83bb0fd')
    def test_get_qos(self):
        """Tests the detail of a given qos-specs"""
        body = self.volume_qos_client.show_qos(self.created_qos['id'])
        self.assertEqual(self.qos_name, body['name'])
        self.assertEqual(self.qos_consumer, body['consumer'])

    @test.attr(type='smoke')
    @test.idempotent_id('75e04226-bcf7-4595-a34b-fdf0736f38fc')
    def test_list_qos(self):
        """Tests the list of all qos-specs"""
        body = self.volume_qos_client.list_qos()
        self.assertIn(self.created_qos, body)

    @test.attr(type='smoke')
    @test.idempotent_id('ed00fd85-4494-45f2-8ceb-9e2048919aed')
    def test_set_unset_qos_key(self):
        """Test the addition of a specs key to qos-specs"""
        args = {'iops_bytes': '500'}
        body = self.volume_qos_client.set_qos_key(self.created_qos['id'],
                                                  iops_bytes='500')
        self.assertEqual(args, body)
        body = self.volume_qos_client.show_qos(self.created_qos['id'])
        self.assertEqual(args['iops_bytes'], body['specs']['iops_bytes'])

        # test the deletion of a specs key from qos-specs
        keys = ['iops_bytes']
        self.volume_qos_client.unset_qos_key(self.created_qos['id'], keys)
        operation = 'qos-key-unset'
        self.volume_qos_client.wait_for_qos_operations(self.created_qos['id'],
                                                       operation, keys)
        body = self.volume_qos_client.show_qos(self.created_qos['id'])
        self.assertNotIn(keys[0], body['specs'])

    @test.attr(type='smoke')
    @test.idempotent_id('1dd93c76-6420-485d-a771-874044c416ac')
    def test_associate_disassociate_qos(self):
        """Test the following operations :

        1. associate_qos
        2. get_association_qos
        3. disassociate_qos
        4. disassociate_all_qos
        """

        # create a test volume-type
        vol_type = []
        for _ in range(0, 3):
            vol_type.append(self._create_test_volume_type())

        # associate the qos-specs with volume-types
        for i in range(0, 3):
            self._test_associate_qos(vol_type[i]['id'])

        # get the association of the qos-specs
        associations = self._test_get_association_qos()

        for i in range(0, 3):
            self.assertIn(vol_type[i]['id'], associations)

        # disassociate a volume-type with qos-specs
        self.volume_qos_client.disassociate_qos(
            self.created_qos['id'], vol_type[0]['id'])
        operation = 'disassociate'
        self.volume_qos_client.wait_for_qos_operations(self.created_qos['id'],
                                                       operation,
                                                       vol_type[0]['id'])
        associations = self._test_get_association_qos()
        self.assertNotIn(vol_type[0]['id'], associations)

        # disassociate all volume-types from qos-specs
        self.volume_qos_client.disassociate_all_qos(
            self.created_qos['id'])
        operation = 'disassociate-all'
        self.volume_qos_client.wait_for_qos_operations(self.created_qos['id'],
                                                       operation)
        associations = self._test_get_association_qos()
        self.assertEmpty(associations)


class QosSpecsV1TestJSON(QosSpecsV2TestJSON):
    _api_version = 1
