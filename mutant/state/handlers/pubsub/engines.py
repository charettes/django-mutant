from __future__ import unicode_literals

import json
from threading import Thread

from django.utils.encoding import force_str


class Redis(Thread):
    channel = 'mutant-state'

    def __init__(self, callback, **options):
        import redis
        super(Redis, self).__init__(name='mutant-state-pubsub-redis-engine')
        self.callback = callback
        self.connection = redis.StrictRedis(**options)
        self.pubsub = self.connection.pubsub()

    def run(self):
        self.pubsub.subscribe(self.channel)
        for event in self.pubsub.listen():
            if event['type'] == 'message':
                args = json.loads(force_str(event['data']))
                self.callback(*args)

    def publish(self, *args):
        message = json.dumps(args)
        self.connection.publish(self.channel, message)

    def join(self, timeout=None):
        self.pubsub.unsubscribe(self.channel)
        return super(Redis, self).join(timeout)
