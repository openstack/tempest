# Copyright 2016 NEC Corporation
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


def get_image_meta_from_headers(resp):
    meta = {'properties': {}}
    for key in resp.response:
        value = resp.response[key]
        if key.startswith('x-image-meta-property-'):
            _key = key[22:]
            meta['properties'][_key] = value
        elif key.startswith('x-image-meta-'):
            _key = key[13:]
            meta[_key] = value

    for key in ['is_public', 'protected', 'deleted']:
        if key in meta:
            meta[key] = meta[key].strip().lower() in ('t', 'true', 'yes', '1')

    for key in ['size', 'min_ram', 'min_disk']:
        if key in meta:
            try:
                meta[key] = int(meta[key])
            except ValueError:
                pass
    return meta
