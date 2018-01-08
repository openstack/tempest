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

# The 2.45 microversion removes the "location" header and adds "image_id"
# to the response body.
create_image = {
    'status_code': [202],
    'response_body': {
        'type': 'object',
        'properties': {
            'image_id': {'type': 'string'}
        },
        'additionalProperties': False,
        'required': ['image_id']
    }
}

# NOTE(mriedem): The compute proxy APIs for showing/listing and deleting
# images were deprecated in microversion 2.35, and the compute proxy APIs for
# working with image metadata were deprecated in microversion 2.39. Therefore,
# client-side code shouldn't rely on those APIs in the compute images client
# past those microversions and should instead use the Glance images client
# directly.
