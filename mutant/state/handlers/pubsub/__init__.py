from __future__ import unicode_literals

import time

from django.utils.module_loading import import_string

from mutant import settings

from ..memory import MemoryStateHandler


class PubSubStateHandler(MemoryStateHandler):
    def __init__(self, engine=None):
        super(PubSubStateHandler, self).__init__()
        dotted_path, options = engine or settings.STATE_PUBSUB
        engine_cls = import_string(dotted_path)
        self.timestamps = {}
        self.engine = engine_cls(self.flush, self.receive, **options)
        self.engine.start()
        while not self.engine.ready:
            time.sleep(0.1)

    def receive(self, definition_pk, checksum, timestamp):
        # Do not alter current state if the change was published before our
        if self.timestamps.get(definition_pk, timestamp) > timestamp:
            return
        if checksum is None:
            super(PubSubStateHandler, self).clear_checksum(definition_pk)
        else:
            super(PubSubStateHandler, self).set_checksum(definition_pk, checksum)

    def set_checksum(self, definition_pk, checksum):
        timestamp = time.time()
        with self.lock:
            self.timestamps[definition_pk] = timestamp
            super(PubSubStateHandler, self).set_checksum(definition_pk, checksum)
        self.engine.publish(definition_pk, checksum, timestamp)

    def clear_checksum(self, definition_pk):
        timestamp = time.time()
        with self.lock:
            self.timestamps[definition_pk] = timestamp
            super(PubSubStateHandler, self).clear_checksum(definition_pk)
        self.engine.publish(definition_pk, None, timestamp)
