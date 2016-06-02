from __future__ import unicode_literals

from threading import RLock


class MemoryStateHandler(object):
    """
    State handler that relies on a lock and an in-memory map of definition
    pk and their associated checksums to maintain the current state of mutable
    models.
    """

    def __init__(self):
        self.lock = RLock()
        self.checksums = {}

    def flush(self):
        with self.lock:
            self.checksums.clear()

    def get_checksum(self, definition_pk):
        return self.checksums.get(definition_pk)

    def set_checksum(self, definition_pk, checksum):
        with self.lock:
            self.checksums[definition_pk] = checksum

    def clear_checksum(self, definition_pk):
        with self.lock:
            try:
                del self.checksums[definition_pk]
            except KeyError:
                pass
