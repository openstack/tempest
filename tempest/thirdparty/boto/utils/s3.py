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

import contextlib
import os
import re

import boto
import boto.s3.key

from oslo_log import log as logging

LOG = logging.getLogger(__name__)


def s3_upload_dir(bucket, path, prefix="", connection_data=None):
    if isinstance(bucket, basestring):
        with contextlib.closing(boto.connect_s3(**connection_data)) as conn:
            bucket = conn.lookup(bucket)
    for root, dirs, files in os.walk(path):
        for fil in files:
            with contextlib.closing(boto.s3.key.Key(bucket)) as key:
                source = root + os.sep + fil
                target = re.sub("^" + re.escape(path) + "?/", prefix, source)
                if os.sep != '/':
                    target = re.sub(re.escape(os.sep), '/', target)
                key.key = target
                LOG.info("Uploading %s to %s/%s", source, bucket.name, target)
                key.set_contents_from_filename(source)
