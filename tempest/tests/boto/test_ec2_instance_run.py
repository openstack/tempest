# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

from contextlib import closing
import logging

from boto.s3.key import Key
import nose
from nose.plugins.attrib import attr
import unittest2 as unittest

from tempest.common.utils.data_utils import rand_name
from tempest.common.utils.linux.remote_client import RemoteClient
from tempest.exceptions import EC2RegisterImageException
from tempest import openstack
from tempest.testboto import BotoTestCase
import tempest.tests.boto
from tempest.tests.boto.utils.s3 import s3_upload_dir
from tempest.tests.boto.utils.wait import re_search_wait
from tempest.tests.boto.utils.wait import state_wait

LOG = logging.getLogger(__name__)


@attr("S3", "EC2")
class InstanceRunTest(BotoTestCase):

    @classmethod
    def setUpClass(cls):
        super(InstanceRunTest, cls).setUpClass()
        if not tempest.tests.boto.A_I_IMAGES_READY:
            raise nose.SkipTest("".join(("EC2 ", cls.__name__,
                                ": requires ami/aki/ari manifest")))
        cls.os = openstack.Manager()
        cls.s3_client = cls.os.s3_client
        cls.ec2_client = cls.os.ec2api_client
        config = cls.os.config
        cls.zone = cls.ec2_client.get_good_zone()
        cls.materials_path = config.boto.s3_materials_path
        ami_manifest = config.boto.ami_manifest
        aki_manifest = config.boto.aki_manifest
        ari_manifest = config.boto.ari_manifest
        cls.instance_type = config.boto.instance_type
        cls.bucket_name = rand_name("s3bucket-")
        cls.keypair_name = rand_name("keypair-")
        cls.keypair = cls.ec2_client.create_key_pair(cls.keypair_name)
        cls.addResourceCleanUp(cls.ec2_client.delete_key_pair,
                               cls.keypair_name)
        bucket = cls.s3_client.create_bucket(cls.bucket_name)
        cls.addResourceCleanUp(cls.destroy_bucket,
                               cls.s3_client.connection_data,
                               cls.bucket_name)
        s3_upload_dir(bucket, cls.materials_path)
        cls.images = {"ami":
                      {"name": rand_name("ami-name-"),
                       "location": cls.bucket_name + "/" + ami_manifest},
                      "aki":
                      {"name": rand_name("aki-name-"),
                       "location": cls.bucket_name + "/" + aki_manifest},
                      "ari":
                      {"name": rand_name("ari-name-"),
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
            state = state_wait(_state, "available")
            if state != "available":
                for _image in cls.images.itervalues():
                    ec2_client.deregister_image(_image["image_id"])
                raise RegisterImageException(image_id=image["image_id"])

    @attr(type='smoke')
    def test_run_stop_terminate_instance(self):
        """EC2 run, stop and terminate instance"""
        image_ami = self.ec2_client.get_image(self.images["ami"]
                                              ["image_id"])
        reservation = image_ami.run(kernel_id=self.images["aki"]["image_id"],
                                    ramdisk_id=self.images["ari"]["image_id"],
                                    instance_type=self.instance_type)
        rcuk = self.addResourceCleanUp(self.destroy_reservation, reservation)

        def _state():
            instance.update(validate=True)
            return instance.state

        for instance in reservation.instances:
            LOG.info("state: %s", instance.state)
            if instance.state != "running":
                self.assertInstanceStateWait(_state, "running")

        for instance in reservation.instances:
            instance.stop()
            LOG.info("state: %s", instance.state)
            if instance.state != "stopped":
                self.assertInstanceStateWait(_state, "stopped")

        for instance in reservation.instances:
            instance.terminate()
        self.cancelResourceCleanUp(rcuk)

    @attr(type='smoke')
    def test_run_terminate_instance(self):
        """EC2 run, terminate immediately"""
        image_ami = self.ec2_client.get_image(self.images["ami"]
                                              ["image_id"])
        reservation = image_ami.run(kernel_id=self.images["aki"]["image_id"],
                                    ramdisk_id=self.images["ari"]["image_id"],
                                    instance_type=self.instance_type)

        for instance in reservation.instances:
            instance.terminate()

        instance.update(validate=True)
        self.assertNotEqual(instance.state, "running")

    #NOTE(afazekas): doctored test case,
    # with normal validation it would fail
    @attr("slow", type='smoke')
    def test_integration_1(self):
        """EC2 1. integration test (not strict)"""
        image_ami = self.ec2_client.get_image(self.images["ami"]["image_id"])
        sec_group_name = rand_name("securitygroup-")
        group_desc = sec_group_name + " security group description "
        security_group = self.ec2_client.create_security_group(sec_group_name,
                                                               group_desc)
        self.addResourceCleanUp(self.destroy_security_group_wait,
                                security_group)
        self.ec2_client.authorize_security_group(sec_group_name,
                                                 ip_protocol="icmp",
                                                 cidr_ip="0.0.0.0/0",
                                                 from_port=-1,
                                                 to_port=-1)
        self.ec2_client.authorize_security_group(sec_group_name,
                                                 ip_protocol="tcp",
                                                 cidr_ip="0.0.0.0/0",
                                                 from_port=22,
                                                 to_port=22)
        reservation = image_ami.run(kernel_id=self.images["aki"]["image_id"],
                                    ramdisk_id=self.images["ari"]["image_id"],
                                    instance_type=self.instance_type,
                                    key_name=self.keypair_name,
                                    security_groups=(sec_group_name,))
        self.addResourceCleanUp(self.destroy_reservation,
                                reservation)
        volume = self.ec2_client.create_volume(1, self.zone)
        self.addResourceCleanUp(self.destroy_volume_wait, volume)
        instance = reservation.instances[0]

        def _instance_state():
            instance.update(validate=True)
            return instance.state

        def _volume_state():
            volume.update(validate=True)
            return volume.status

        LOG.info("state: %s", instance.state)
        if instance.state != "running":
            self.assertInstanceStateWait(_instance_state, "running")

        address = self.ec2_client.allocate_address()
        rcuk_a = self.addResourceCleanUp(address.delete)
        address.associate(instance.id)

        rcuk_da = self.addResourceCleanUp(address.disassociate)
        #TODO(afazekas): ping test. dependecy/permission ?

        self.assertVolumeStatusWait(_volume_state, "available")
        #NOTE(afazekas): it may be reports availble before it is available

        ssh = RemoteClient(address.public_ip,
                           self.os.config.compute.ssh_user,
                           pkey=self.keypair.material)
        text = rand_name("Pattern text for console output -")
        resp = ssh.write_to_console(text)
        self.assertFalse(resp)

        def _output():
            output = instance.get_console_output()
            return output.output

        re_search_wait(_output, text)
        part_lines = ssh.get_partitions().split('\n')
        # "attaching" invalid EC2 state ! #1074901
        volume.attach(instance.id, "/dev/vdh")

        #self.assertVolumeStatusWait(_volume_state, "in-use")  # #1074901
        re_search_wait(_volume_state, "in-use")

        #NOTE(afazekas):  Different Hypervisor backends names
        # differently the devices,
        # now we just test is the partition number increased/decrised

        def _part_state():
            current = ssh.get_partitions().split('\n')
            if current > part_lines:
                return 'INCREASE'
            if current < part_lines:
                return 'DECREASE'
            return 'EQUAL'

        state_wait(_part_state, 'INCREASE')
        part_lines = ssh.get_partitions().split('\n')

        #TODO(afazekas): Resource compare to the flavor settings

        volume.detach()  # "detaching" invalid EC2 status #1074901

        #self.assertVolumeStatusWait(_volume_state, "available")
        re_search_wait(_volume_state, "available")
        LOG.info("Volume %s state: %s", volume.id, volume.status)

        state_wait(_part_state, 'DECREASE')

        instance.stop()
        address.disassociate()
        self.assertAddressDissasociatedWait(address)
        self.cancelResourceCleanUp(rcuk_da)
        address.release()
        self.assertAddressReleasedWait(address)
        self.cancelResourceCleanUp(rcuk_a)

        LOG.info("state: %s", instance.state)
        if instance.state != "stopped":
            self.assertInstanceStateWait(_instance_state, "stopped")
        #TODO(afazekas): move steps from teardown to the test case


#TODO(afazekas): Snapshot/volume read/write test case
