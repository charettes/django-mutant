from __future__ import unicode_literals

import sys
import time

# TODO: Remove when support for Python 2.6 is dropped
if sys.version_info >= (2, 7):
    from unittest import skipUnless
else:
    from django.utils.unittest import skipUnless

from django.utils.functional import cached_property
from django.utils.module_loading import import_by_path

from mutant.state import handler as state_handler
from mutant.state.handlers.pubsub import engines as pubsub_engines

from .utils import BaseModelDefinitionTestCase

try:
    import redis
except ImportError:
    redis_installed = False
else:
    redis_installed = True


class StateHandlerTestMixin(object):
    def setUp(self):
        super(StateHandlerTestMixin, self).setUp()
        self._state_handler = state_handler.path
        state_handler.path = self.handler_path

    def tearDown(self):
        state_handler.path = self._state_handler
        super(StateHandlerTestMixin, self).tearDown()

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


class MemoryHandlerTest(StateHandlerTestMixin, BaseModelDefinitionTestCase):
    handler_path = 'mutant.state.handlers.memory.MemoryStateHandler'


class CacheHandlerTest(StateHandlerTestMixin, BaseModelDefinitionTestCase):
    handler_path = 'mutant.state.handlers.cache.CacheStateHandler'


@skipUnless(redis_installed, 'This state handler requires redis to be installed.')
class PubsubHandlerTest(StateHandlerTestMixin, BaseModelDefinitionTestCase):
    handler_path = 'mutant.state.handlers.pubsub.PubSubStateHandler'

    def test_obsolesence_do_not_clear_checksum(self):
        messages = []

        def add_message(*args):
            messages.append(args)
        engine = pubsub_engines.Redis(add_message)
        model_class = self.model_def.model_class()
        engine.start()
        time.sleep(1)  # Give it some time to subscribe
        model_class.mark_as_obsolete()
        engine.join()
        self.assertEqual(len(messages), 0)
