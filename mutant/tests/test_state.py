from __future__ import unicode_literals

import sys

# TODO: Remove when support for Python 2.6 is dropped
if sys.version_info >= (2, 7):
    from unittest import TestCase, skipUnless
else:
    from django.utils.unittest import TestCase, skipUnless

from django.utils.functional import cached_property
from django.utils.module_loading import import_by_path

try:
    import redis
except ImportError:
    redis_installed = False
else:
    redis_installed = True


class StateHandlerTestMixin(object):
    @cached_property
    def handler(self):
        return import_by_path(self.handler_path)()

    def test_basic_interaction(self):
        self.assertIsNone(self.handler.get_checksum(0))
        checksum = '397fc6229a59429ee114441b780fe7a2'
        self.handler.set_checksum(0, checksum)
        self.assertEqual(self.handler.get_checksum(0), checksum)
        self.handler.clear_checksum(0)
        self.assertIsNone(self.handler.get_checksum(0))


class MemoryHandlerTest(StateHandlerTestMixin, TestCase):
    handler_path = 'mutant.state.handlers.memory.MemoryStateHandler'


class CacheHandlerTest(StateHandlerTestMixin, TestCase):
    handler_path = 'mutant.state.handlers.cache.CacheStateHandler'


@skipUnless(redis_installed, 'This state handler requires redis to be installed.')
class PubsubHandlerTest(StateHandlerTestMixin, TestCase):
    handler_path = 'mutant.state.handlers.pubsub.PubSubStateHandler'
