# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack, LLC
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

"""Functional test case to check RabbitMQ """
import pika
import tests

from pprint import pprint
#RABBITMQ_HOST = get_config("rabbitmq/host")
#RABBITMQ_USERNAME = get_config("rabbitmq/user")
#RABBITMQ_PASSWORD = get_config("rabbitmq/password")


class TestRabbitMQ(tests.FunctionalTest):
    def test_000_ghetto(self):
        """
        This sets the host, user, and pass self variables so they
        are accessible by all other methods
        """
        self.rabbitmq['host'] = self.config['rabbitmq']['host']
        self.rabbitmq['user'] = self.config['rabbitmq']['user']
        self.rabbitmq['pass'] = self.config['rabbitmq']['password']
    test_000_ghetto.tags = ['rabbitmq']

    def _cnx(self):
        # TODO: Figuring out what's going with creds
        # creds = pika.credentials.PlainCredentials(
        #     self.rabbitmq['user'], self.rabbitmq['pass']
        connection = pika.BlockingConnection(pika.ConnectionParameters(
                host=self.rabbitmq['host']))
        channel = connection.channel()
        return (channel, connection)

    def test_001_connect(self):
        channel, connection = self._cnx()
        self.assert_(channel)
        connection.close()
    test_001_connect.tags = ['rabbitmq']

    def test_002_send_receive_msg(self):
        unitmsg = 'Hello from unittest'
        channel, connection = self._cnx()
        channel.queue_declare(queue='u1')
        channel.basic_publish(exchange='',
                              routing_key='u1',
                              body=unitmsg)
        connection.close()

        channel, connection = self._cnx()

        def callback(ch, method, properties, body):
            self.assertEquals(body, unitmsg)
            ch.stop_consuming()

        channel.basic_consume(callback,
                              queue='u1',
                              no_ack=True)
        channel.start_consuming()
    test_002_send_receive_msg.tags = ['rabbitmq']

    def test_003_send_receive_msg_with_persistense(self):
        unitmsg = 'Hello from unittest with Persistense'
        channel, connection = self._cnx()
        channel.queue_declare(queue='u2', durable=True)
        prop = pika.BasicProperties(delivery_mode=2)
        channel.basic_publish(exchange='',
                              routing_key='u2',
                              body=unitmsg,
                              properties=prop,
                              )
        connection.close()

        channel, connection = self._cnx()
        channel.queue_declare(queue='u2', durable=True)

        def callback(ch, method, properties, body):
            self.assertEquals(body, unitmsg)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            ch.stop_consuming()

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(callback,
                              queue='u2')

        channel.start_consuming()
    test_003_send_receive_msg_with_persistense.tags = ['rabbitmq']
