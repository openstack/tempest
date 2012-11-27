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

import boto
from boto.s3.connection import OrdinaryCallingFormat
from boto.ec2.regioninfo import RegionInfo
from tempest.services.boto import BotoClientBase
import urlparse


class APIClientEC2(BotoClientBase):

    def connect_method(self, *args, **kwargs):
        return boto.connect_ec2(*args, **kwargs)

    def __init__(self, config, *args, **kwargs):
        super(APIClientEC2, self).__init__(config, *args, **kwargs)
        aws_access = config.boto.aws_access
        aws_secret = config.boto.aws_secret
        purl = urlparse.urlparse(config.boto.ec2_url)

        region = RegionInfo(name=config.boto.aws_region,
                            endpoint=purl.hostname)
        port = purl.port
        if port is None:
            if purl.scheme is not "https":
                port = 80
            else:
                port = 443
        else:
            port = int(port)
        self.connection_data = {"aws_access_key_id": aws_access,
                                "aws_secret_access_key": aws_secret,
                                "is_secure": purl.scheme == "https",
                                "region": region,
                                "host": purl.hostname,
                                "port": port,
                                "path": purl.path}

    ALLOWED_METHODS = set(('create_key_pair', 'get_key_pair',
                           'delete_key_pair', 'import_key_pair',
                           'get_all_key_pairs',
                           'create_image', 'get_image',
                           'register_image', 'deregister_image',
                           'get_all_images', 'get_image_attribute',
                           'modify_image_attribute', 'reset_image_attribute',
                           'get_all_kernels',
                           'create_volume', 'delete_volume',
                           'get_all_volume_status', 'get_all_volumes',
                           'get_volume_attribute', 'modify_volume_attribute'
                           'bundle_instance', 'cancel_spot_instance_requests',
                           'confirm_product_instanc',
                           'get_all_instance_status', 'get_all_instances',
                           'get_all_reserved_instances',
                           'get_all_spot_instance_requests',
                           'get_instance_attribute', 'monitor_instance',
                           'monitor_instances', 'unmonitor_instance',
                           'unmonitor_instances',
                           'purchase_reserved_instance_offering',
                           'reboot_instances', 'request_spot_instances',
                           'reset_instance_attribute', 'run_instances',
                           'start_instances', 'stop_instances',
                           'terminate_instances',
                           'attach_network_interface', 'attach_volume',
                           'detach_network_interface', 'detach_volume',
                           'get_console_output',
                           'delete_network_interface', 'create_subnet',
                           'create_network_interface', 'delete_subnet',
                           'get_all_network_interfaces',
                           'allocate_address', 'associate_address',
                           'disassociate_address', 'get_all_addresses',
                           'release_address',
                           'create_snapshot', 'delete_snapshot',
                           'get_all_snapshots', 'get_snapshot_attribute',
                           'modify_snapshot_attribute',
                           'reset_snapshot_attribute', 'trim_snapshots',
                           'get_all_regions', 'get_all_zones',
                           'get_all_security_groups', 'create_security_group',
                           'delete_security_group', 'authorize_security_group',
                           'authorize_security_group_egress',
                           'revoke_security_group',
                           'revoke_security_group_egress'))

    def get_good_zone(self):
        """
        :rtype: BaseString
        :return: Returns with the first available zone name
        """
        for zone in self.get_all_zones():
            #NOTE(afazekas): zone.region_name was None
            if (zone.state == "available" and
                zone.region.name == self.connection_data["region"].name):
                return zone.name
        else:
            raise IndexError("Don't have a good zone")


class ObjectClientS3(BotoClientBase):

    def connect_method(self, *args, **kwargs):
        return boto.connect_s3(*args, **kwargs)

    def __init__(self, config, *args, **kwargs):
        super(ObjectClientS3, self).__init__(config, *args, **kwargs)
        aws_access = config.boto.aws_access
        aws_secret = config.boto.aws_secret
        purl = urlparse.urlparse(config.boto.s3_url)
        port = purl.port
        if port is None:
            if purl.scheme is not "https":
                port = 80
            else:
                port = 443
        else:
            port = int(port)
        self.connection_data = {"aws_access_key_id": aws_access,
                                "aws_secret_access_key": aws_secret,
                                "is_secure": purl.scheme == "https",
                                "host": purl.hostname,
                                "port": port,
                                "calling_format": OrdinaryCallingFormat()}

    ALLOWED_METHODS = set(('create_bucket', 'delete_bucket', 'generate_url',
                           'get_all_buckets', 'get_bucket', 'delete_key',
                           'lookup'))
