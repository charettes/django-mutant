from __future__ import unicode_literals

from time import time

from django.utils.module_loading import import_string

from mutant import settings

from ..memory import MemoryStateHandler


class PubSubStateHandler(MemoryStateHandler):
    timestamps = {}

    def __init__(self):
        super(PubSubStateHandler, self).__init__()
        dotted_path, options = settings.STATE_PUBSUB
        engine_cls = import_string(dotted_path)
        self.engine = engine_cls(self.receive, **options)
        self.engine.start()

    def receive(self, definition_pk, checksum, timestamp):
        # Do not alter current state if the change was published before our
        if self.timestamps.get(definition_pk, timestamp) > timestamp:
            return
        if checksum is None:
            super(PubSubStateHandler, self).clear_checksum(definition_pk)
        else:
            super(PubSubStateHandler, self).set_checksum(definition_pk, checksum)

    def set_checksum(self, definition_pk, checksum):
        timestamp = time()
        with self.lock:
            self.timestamps[definition_pk] = timestamp
            super(PubSubStateHandler, self).set_checksum(definition_pk, checksum)
        self.engine.publish(definition_pk, checksum, timestamp)

    def clear_checksum(self, definition_pk):
        timestamp = time()
        with self.lock:
            self.timestamps[definition_pk] = timestamp
            super(PubSubStateHandler, self).clear_checksum(definition_pk)
        self.engine.publish(definition_pk, None, timestamp)
