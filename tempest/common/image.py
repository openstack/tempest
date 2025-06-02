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

import copy
from http import server
import random
import threading
import time


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


def image_meta_to_headers(**metadata):
    headers = {}
    fields_copy = copy.deepcopy(metadata)

    copy_from = fields_copy.pop('copy_from', None)
    purge = fields_copy.pop('purge_props', None)

    if purge is not None:
        headers['x-glance-registry-purge-props'] = purge

    if copy_from is not None:
        headers['x-glance-api-copy-from'] = copy_from

    for key, value in fields_copy.pop('properties', {}).items():
        headers['x-image-meta-property-%s' % key] = str(value)

    for key, value in fields_copy.pop('api', {}).items():
        headers['x-glance-api-property-%s' % key] = str(value)

    for key, value in fields_copy.items():
        headers['x-image-meta-%s' % key] = str(value)

    return headers


class RandomDataHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/octet-stream')
        self.end_headers()

        start_time = time.time()
        chunk_size = 64 * 1024  # 64 KiB per chunk
        while time.time() - start_time < 60:
            data = bytes(random.getrandbits(8) for _ in range(chunk_size))
            try:
                self.wfile.write(data)
                self.wfile.flush()
                # simulate slow transfer
                time.sleep(0.2)
            except BrokenPipeError:
                # Client disconnected; stop sending data
                break

    def do_HEAD(self):
        # same size as in do_GET (19,660,800 bytes (about 18.75 MiB)
        size = 300 * 65536
        self.send_response(200)
        self.send_header('Content-Type', 'application/octet-stream')
        self.send_header('Content-Length', str(size))
        self.end_headers()


class RandomDataServer(object):
    def __init__(self, handler_class=RandomDataHandler):
        self.handler_class = handler_class
        self.server = None
        self.thread = None
        self.port = None

    def start(self):
        # Bind to port 0 for an unused port
        self.server = server.HTTPServer(('localhost', 0), self.handler_class)
        self.port = self.server.server_address[1]

        # Run server in background thread
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.thread.join()
            self.server = None
            self.thread = None
