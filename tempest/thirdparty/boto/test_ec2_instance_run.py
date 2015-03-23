# Copyright 2012 OpenStack Foundation
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

from oslo_log import log as logging
from tempest_lib.common.utils import data_utils

from tempest.common.utils.linux import remote_client
from tempest import config
from tempest import exceptions
from tempest import test
from tempest.thirdparty.boto import test as boto_test
from tempest.thirdparty.boto.utils import s3
from tempest.thirdparty.boto.utils import wait

CONF = config.CONF

LOG = logging.getLogger(__name__)


class InstanceRunTest(boto_test.BotoTestCase):

    @classmethod
    def setup_clients(cls):
        super(InstanceRunTest, cls).setup_clients()
        cls.s3_client = cls.os.s3_client
        cls.ec2_client = cls.os.ec2api_client

    @classmethod
    def resource_setup(cls):
        super(InstanceRunTest, cls).resource_setup()
        if not cls.conclusion['A_I_IMAGES_READY']:
            raise cls.skipException("".join(("EC2 ", cls.__name__,
                                    ": requires ami/aki/ari manifest")))
        cls.zone = CONF.boto.aws_zone
        cls.materials_path = CONF.boto.s3_materials_path
        ami_manifest = CONF.boto.ami_manifest
        aki_manifest = CONF.boto.aki_manifest
        ari_manifest = CONF.boto.ari_manifest
        cls.instance_type = CONF.boto.instance_type
        cls.bucket_name = data_utils.rand_name("s3bucket")
        cls.keypair_name = data_utils.rand_name("keypair")
        cls.keypair = cls.ec2_client.create_key_pair(cls.keypair_name)
        cls.addResourceCleanUp(cls.ec2_client.delete_key_pair,
                               cls.keypair_name)
        bucket = cls.s3_client.create_bucket(cls.bucket_name)
        cls.addResourceCleanUp(cls.destroy_bucket,
                               cls.s3_client.connection_data,
                               cls.bucket_name)
        s3.s3_upload_dir(bucket, cls.materials_path)
        cls.images = {"ami":
                      {"name": data_utils.rand_name("ami-name"),
                       "location": cls.bucket_name + "/" + ami_manifest},
                      "aki":
                      {"name": data_utils.rand_name("aki-name"),
                       "location": cls.bucket_name + "/" + aki_manifest},
                      "ari":
                      {"name": data_utils.rand_name("ari-name"),
                       "location": cls.bucket_name + "/" + ari_manifest}}
        for image in cls.images.itervalues():
            image["image_id"] = cls.ec2_client.register_image(
                name=image["name"],
                image_location=image["location"])
            cls.addResourceCleanUp(cls.ec2_client.deregister_image,
                                   image["image_id"])

        for image in cls.images.itervalues():
            def _state():
                retr = cls.ec2_client.get_image(image["image_id"])
                return retr.state
            state = wait.state_wait(_state, "available")
            if state != "available":
                for _image in cls.images.itervalues():
                    cls.ec2_client.deregister_image(_image["image_id"])
                raise exceptions.EC2RegisterImageException(
                    image_id=image["image_id"])

    def _terminate_reservation(self, reservation, rcuk):
        for instance in reservation.instances:
            instance.terminate()
        for instance in reservation.instances:
            self.assertInstanceStateWait(instance, '_GONE')
        self.cancelResourceCleanUp(rcuk)

    @test.idempotent_id('c881fbb7-d56e-4054-9d76-1c3a60a207b0')
    def test_run_idempotent_instances(self):
        # EC2 run instances idempotently

        def _run_instance(client_token):
            reservation = self.ec2_client.run_instances(
                image_id=self.images["ami"]["image_id"],
                kernel_id=self.images["aki"]["image_id"],
                ramdisk_id=self.images["ari"]["image_id"],
                instance_type=self.instance_type,
                client_token=client_token)
            rcuk = self.addResourceCleanUp(self.destroy_reservation,
                                           reservation)
            return (reservation, rcuk)

        reservation_1, rcuk_1 = _run_instance('token_1')
        reservation_2, rcuk_2 = _run_instance('token_2')
        reservation_1a, rcuk_1a = _run_instance('token_1')

        self.assertIsNotNone(reservation_1)
        self.assertIsNotNone(reservation_2)
        self.assertIsNotNone(reservation_1a)

        # same reservation for token_1
        self.assertEqual(reservation_1.id, reservation_1a.id)

        # Cancel cleanup -- since it's a duplicate, it's
        # handled by rcuk1
        self.cancelResourceCleanUp(rcuk_1a)

        self._terminate_reservation(reservation_1, rcuk_1)
        self._terminate_reservation(reservation_2, rcuk_2)

    @test.idempotent_id('2ea26a39-f96c-48fc-8374-5c10ec184c67')
    def test_run_stop_terminate_instance(self):
        # EC2 run, stop and terminate instance
        image_ami = self.ec2_client.get_image(self.images["ami"]
                                              ["image_id"])
        reservation = image_ami.run(kernel_id=self.images["aki"]["image_id"],
                                    ramdisk_id=self.images["ari"]["image_id"],
                                    instance_type=self.instance_type)
        rcuk = self.addResourceCleanUp(self.destroy_reservation, reservation)

        for instance in reservation.instances:
            LOG.info("state: %s", instance.state)
            if instance.state != "running":
                self.assertInstanceStateWait(instance, "running")

        for instance in reservation.instances:
            instance.stop()
            LOG.info("state: %s", instance.state)
            if instance.state != "stopped":
                self.assertInstanceStateWait(instance, "stopped")

        self._terminate_reservation(reservation, rcuk)

    @test.idempotent_id('3d77225a-5cec-4e54-a017-9ebf11a266e6')
    def test_run_stop_terminate_instance_with_tags(self):
        # EC2 run, stop and terminate instance with tags
        image_ami = self.ec2_client.get_image(self.images["ami"]
                                              ["image_id"])
        reservation = image_ami.run(kernel_id=self.images["aki"]["image_id"],
                                    ramdisk_id=self.images["ari"]["image_id"],
                                    instance_type=self.instance_type)
        rcuk = self.addResourceCleanUp(self.destroy_reservation, reservation)

        for instance in reservation.instances:
            LOG.info("state: %s", instance.state)
            if instance.state != "running":
                self.assertInstanceStateWait(instance, "running")
            instance.add_tag('key1', value='value1')

        tags = self.ec2_client.get_all_tags()
        td = {item.name: item.value for item in tags}

        self.assertIn('key1', td)
        self.assertEqual('value1', td['key1'])

        tags = self.ec2_client.get_all_tags(filters={'key': 'key1'})
        td = {item.name: item.value for item in tags}
        self.assertIn('key1', td)
        self.assertEqual('value1', td['key1'])

        tags = self.ec2_client.get_all_tags(filters={'value': 'value1'})
        td = {item.name: item.value for item in tags}
        self.assertIn('key1', td)
        self.assertEqual('value1', td['key1'])

        tags = self.ec2_client.get_all_tags(filters={'key': 'value2'})
        td = {item.name: item.value for item in tags}
        self.assertNotIn('key1', td)

        for instance in reservation.instances:
            instance.remove_tag('key1', value='value1')

        tags = self.ec2_client.get_all_tags()

        # NOTE: Volume-attach and detach causes metadata (tags) to be created
        # for the volume. So exclude them while asserting.
        self.assertNotIn('key1', tags)

        for instance in reservation.instances:
            instance.stop()
            LOG.info("state: %s", instance.state)
            if instance.state != "stopped":
                self.assertInstanceStateWait(instance, "stopped")

        self._terminate_reservation(reservation, rcuk)

    @test.idempotent_id('252945b5-3294-4fda-ae21-928a42f63f76')
    def test_run_terminate_instance(self):
        # EC2 run, terminate immediately
        image_ami = self.ec2_client.get_image(self.images["ami"]
                                              ["image_id"])
        reservation = image_ami.run(kernel_id=self.images["aki"]["image_id"],
                                    ramdisk_id=self.images["ari"]["image_id"],
                                    instance_type=self.instance_type)

        for instance in reservation.instances:
            instance.terminate()
        self.assertInstanceStateWait(instance, '_GONE')

    @test.idempotent_id('ab836c29-737b-4101-9fb9-87045eaf89e9')
    def test_compute_with_volumes(self):
        # EC2 1. integration test (not strict)
        image_ami = self.ec2_client.get_image(self.images["ami"]["image_id"])
        sec_group_name = data_utils.rand_name("securitygroup")
        group_desc = sec_group_name + " security group description "
        security_group = self.ec2_client.create_security_group(sec_group_name,
                                                               group_desc)
        self.addResourceCleanUp(self.destroy_security_group_wait,
                                security_group)
        self.assertTrue(
            self.ec2_client.authorize_security_group(
                sec_group_name,
                ip_protocol="icmp",
                cidr_ip="0.0.0.0/0",
                from_port=-1,
                to_port=-1))
        self.assertTrue(
            self.ec2_client.authorize_security_group(
                sec_group_name,
                ip_protocol="tcp",
                cidr_ip="0.0.0.0/0",
                from_port=22,
                to_port=22))
        reservation = image_ami.run(kernel_id=self.images["aki"]["image_id"],
                                    ramdisk_id=self.images["ari"]["image_id"],
                                    instance_type=self.instance_type,
                                    key_name=self.keypair_name,
                                    security_groups=(sec_group_name,))

        LOG.debug("Instance booted - state: %s",
                  reservation.instances[0].state)

        self.addResourceCleanUp(self.destroy_reservation,
                                reservation)
        volume = self.ec2_client.create_volume(CONF.volume.volume_size,
                                               self.zone)
        LOG.debug("Volume created - status: %s", volume.status)

        self.addResourceCleanUp(self.destroy_volume_wait, volume)
        instance = reservation.instances[0]
        if instance.state != "running":
            self.assertInstanceStateWait(instance, "running")
        LOG.debug("Instance now running - state: %s", instance.state)

        address = self.ec2_client.allocate_address()
        rcuk_a = self.addResourceCleanUp(address.delete)
        self.assertTrue(address.associate(instance.id))

        rcuk_da = self.addResourceCleanUp(address.disassociate)
        # TODO(afazekas): ping test. dependecy/permission ?

        self.assertVolumeStatusWait(volume, "available")
        # NOTE(afazekas): it may be reports available before it is available

        ssh = remote_client.RemoteClient(address.public_ip,
                                         CONF.compute.ssh_user,
                                         pkey=self.keypair.material)
        text = data_utils.rand_name("Pattern text for console output")
        resp = ssh.write_to_console(text)
        self.assertFalse(resp)

        def _output():
            output = instance.get_console_output()
            return output.output

        wait.re_search_wait(_output, text)
        part_lines = ssh.get_partitions().split('\n')
        volume.attach(instance.id, "/dev/vdh")

        def _volume_state():
            """Return volume state realizing that 'in-use' is overloaded."""
            volume.update(validate=True)
            status = volume.status
            attached = volume.attach_data.status
            LOG.debug("Volume %s is in status: %s, attach_status: %s",
                      volume.id, status, attached)
            # Nova reports 'in-use' on 'attaching' volumes because we
            # have a single volume status, and EC2 has 2. Ensure that
            # if we aren't attached yet we return something other than
            # 'in-use'
            if status == 'in-use' and attached != 'attached':
                return 'attaching'
            else:
                return status

        wait.re_search_wait(_volume_state, "in-use")

        # NOTE(afazekas):  Different Hypervisor backends names
        # differently the devices,
        # now we just test is the partition number increased/decrised

        def _part_state():
            current = ssh.get_partitions().split('\n')
            LOG.debug("Partition map for instance: %s", current)
            if current > part_lines:
                return 'INCREASE'
            if current < part_lines:
                return 'DECREASE'
            return 'EQUAL'

        wait.state_wait(_part_state, 'INCREASE')
        part_lines = ssh.get_partitions().split('\n')

        # TODO(afazekas): Resource compare to the flavor settings

        volume.detach()

        self.assertVolumeStatusWait(volume, "available")

        wait.state_wait(_part_state, 'DECREASE')

        instance.stop()
        address.disassociate()
        self.assertAddressDissasociatedWait(address)
        self.cancelResourceCleanUp(rcuk_da)
        address.release()
        self.assertAddressReleasedWait(address)
        self.cancelResourceCleanUp(rcuk_a)

        LOG.debug("Instance %s state: %s", instance.id, instance.state)
        if instance.state != "stopped":
            self.assertInstanceStateWait(instance, "stopped")
        # TODO(afazekas): move steps from teardown to the test case


# TODO(afazekas): Snapshot/volume read/write test case
