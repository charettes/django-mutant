from __future__ import unicode_literals

import json
import logging
import math
import time
from threading import Thread

import redis
from django.utils.encoding import force_str

logger = logging.getLogger(__name__)


class BaseEngine(Thread):
    def __init__(self, initialize, callback):
        self.initialize = initialize
        self.callback = callback
        self.ready = False
        super(BaseEngine, self).__init__(name="%s.%s" % (self.__module__, self.__class__.__name__))

    def _initialize(self):
        self.initialize()
        self.ready = True

    def stop(self, timeout=None):
        self.join(timeout)

    def publish(self, *args):
        raise NotImplementedError


class Redis(BaseEngine):
    def __init__(self, initialize, callback, channel='mutant-state',
                 socket_timeout=60*10, socket_keepalive=True, **options):
        super(Redis, self).__init__(initialize, callback)
        self.redis = redis.StrictRedis(
            socket_timeout=socket_timeout,
            socket_keepalive=socket_keepalive,
            retry_on_timeout=False,
            **options
        )
        self.socket_timeout = socket_timeout
        self.channel = channel
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(self.channel)

    def _run(self):
        self._initialize()
        for event in self.pubsub.listen():
            if event['type'] == 'message':
                args = json.loads(force_str(event['data']))
                self.callback(*args)

    def _reconnect(self):
        connection = self.pubsub.connection
        if connection:
            connection.disconnect()
        while True:
            logger.info('Attempting to reconnect.')
            try:
                connection.connect()
            except redis.ConnectionError:
                logger.exception('Failed to reconnect, will re-attempt in 5 seconds.')
                time.sleep(5)
            else:
                logger.info('Successfully reconnected.')
                break

    def run(self):
        start = time.time()
        try:
            self._run()
        except redis.TimeoutError:
            if math.ceil(time.time() - start) < self.socket_timeout:
                logger.warning('Unexpected connection timeout.')
            self._reconnect()
            self.run()
        except redis.ConnectionError:
            logger.warning('Connection error.')
            self._reconnect()
            self.run()

    def publish(self, *args):
        message = json.dumps(args)
        self.redis.publish(self.channel, message)

    def join(self, timeout=None):
        self.pubsub.unsubscribe(self.channel)
        super(Redis, self).join(timeout=None)
