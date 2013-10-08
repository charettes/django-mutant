from __future__ import unicode_literals

from django.core.cache import get_cache

from ...settings import STATE_CACHE_ALIAS


class CacheStateHandler(object):
    """State handlers that relies on cache to store and retrieve the current
    checksum of a definition."""

    def get_cache(self):
        return get_cache(STATE_CACHE_ALIAS)

    def get_cache_key(self, definition_pk):
        return "mutant-%s" % definition_pk

    def get_checksum(self, definition_pk):
        cache_key = self.get_cache_key(definition_pk)
        return self.get_cache().get(cache_key)

    def set_checksum(self, definition_pk, checksum):
        cache_key = self.get_cache_key(definition_pk)
        return self.get_cache().set(cache_key, checksum)

    def clear_checksum(self, definition_pk):
        cache_key = self.get_cache_key(definition_pk)
        return self.get_cache().delete(cache_key)
