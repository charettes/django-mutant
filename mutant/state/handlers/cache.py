from __future__ import unicode_literals

from django.core.cache import caches

from ...settings import STATE_CACHE_ALIAS


class CacheStateHandler(object):
    """
    State handlers that relies on cache to store and retrieve the current
    checksum of a definition."
    """

    def __init__(self):
        self.cache = caches[STATE_CACHE_ALIAS]

    def get_cache_key(self, definition_pk):
        return "mutant-%s" % definition_pk

    def get_checksum(self, definition_pk):
        cache_key = self.get_cache_key(definition_pk)
        return self.cache.get(cache_key)

    def set_checksum(self, definition_pk, checksum):
        cache_key = self.get_cache_key(definition_pk)
        return self.cache.set(cache_key, checksum)

    def clear_checksum(self, definition_pk):
        cache_key = self.get_cache_key(definition_pk)
        return self.cache.delete(cache_key)
