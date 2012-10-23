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

import tempest.config
from tempest.common.utils.file_utils import have_effective_read_access
import os
import tempest.openstack
import re
import keystoneclient.exceptions
import boto.exception
import logging
import urlparse

A_I_IMAGES_READY = False  # ari,ami,aki
S3_CAN_CONNECT_ERROR = "Unknown Error"
EC2_CAN_CONNECT_ERROR = "Unknown Error"


def setup_package():
    global A_I_IMAGES_READY
    global S3_CAN_CONNECT_ERROR
    global EC2_CAN_CONNECT_ERROR
    secret_matcher = re.compile("[A-Za-z0-9+/]{32,}")  # 40 in other system
    id_matcher = re.compile("[A-Za-z0-9]{20,}")

    def all_read(*args):
        return all(map(have_effective_read_access, args))

    config = tempest.config.TempestConfig()
    materials_path = config.boto.s3_materials_path
    ami_path = materials_path + os.sep + config.boto.ami_manifest
    aki_path = materials_path + os.sep + config.boto.aki_manifest
    ari_path = materials_path + os.sep + config.boto.ari_manifest

    A_I_IMAGES_READY = all_read(ami_path, aki_path, ari_path)
    boto_logger = logging.getLogger('boto')
    level = boto_logger.level
    boto_logger.setLevel(logging.CRITICAL)  # suppress logging for these

    def _cred_sub_check(connection_data):
        if not id_matcher.match(connection_data["aws_access_key_id"]):
            raise Exception("Invalid AWS access Key")
        if not secret_matcher.match(connection_data["aws_secret_access_key"]):
            raise Exception("Invalid AWS secret Key")
        raise Exception("Unknown (Authentication?) Error")
    openstack = tempest.openstack.Manager()
    try:
        if urlparse.urlparse(config.boto.ec2_url).hostname is None:
            raise Exception("Failed to get hostname from the ec2_url")
        ec2client = openstack.ec2api_client
        try:
            ec2client.get_all_regions()
        except boto.exception.BotoServerError as exc:
                if exc.error_code is None:
                    raise Exception("EC2 target does not looks EC2 service")
                _cred_sub_check(ec2client.connection_data)

    except keystoneclient.exceptions.Unauthorized:
        EC2_CAN_CONNECT_ERROR = "AWS credentials not set," +\
                                " faild to get them even by keystoneclient"
    except Exception as exc:
        logging.exception(exc)
        EC2_CAN_CONNECT_ERROR = str(exc)
    else:
        EC2_CAN_CONNECT_ERROR = None

    try:
        if urlparse.urlparse(config.boto.s3_url).hostname is None:
            raise Exception("Failed to get hostname from the s3_url")
        s3client = openstack.s3_client
        try:
            s3client.get_bucket("^INVALID*#()@INVALID.")
        except  boto.exception.BotoServerError as exc:
            if exc.status == 403:
                _cred_sub_check(s3client.connection_data)
    except Exception as exc:
        logging.exception(exc)
        S3_CAN_CONNECT_ERROR = str(exc)
    except keystoneclient.exceptions.Unauthorized:
        S3_CAN_CONNECT_ERROR = "AWS credentials not set," +\
                               " faild to get them even by keystoneclient"
    else:
        S3_CAN_CONNECT_ERROR = None
    boto_logger.setLevel(level)
