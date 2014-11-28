from __future__ import unicode_literals

import sys
import time
from threading import Thread

# TODO: Remove when support for Python 2.6 is dropped
if sys.version_info >= (2, 7):
    from unittest import skipUnless
else:
    from django.utils.unittest import skipUnless

from mutant.state import handler as state_handler
from mutant.state.handlers.pubsub import engines as pubsub_engines

from .utils import BaseModelDefinitionTestCase

try:
    import redis
except ImportError:
    redis = None


class StateHandlerTestMixin(object):
    def setUp(self):
        super(StateHandlerTestMixin, self).setUp()
        self._state_handler = state_handler.path
        state_handler.path = self.handler_path

    def tearDown(self):
        state_handler.path = self._state_handler
        super(StateHandlerTestMixin, self).tearDown()

    def test_basic_interaction(self):
        self.assertIsNone(state_handler.get_checksum(0))
        checksum = '397fc6229a59429ee114441b780fe7a2'
        state_handler.set_checksum(0, checksum)
        self.assertEqual(state_handler.get_checksum(0), checksum)
        state_handler.clear_checksum(0)
        self.assertIsNone(state_handler.get_checksum(0))


class ChecksumGetter(Thread):
    """Class used to fetch a checksum from a another thread since state
    handler instances are thread local."""

    def __init__(self, definition_pk, *args, **kwargs):
        super(ChecksumGetter, self).__init__(*args, **kwargs)
        self.definition_pk = definition_pk
        self.checksum = None

    def run(self):
        self.checksum = state_handler.get_checksum(self.definition_pk)


class MemoryHandlerTest(StateHandlerTestMixin, BaseModelDefinitionTestCase):
    handler_path = 'mutant.state.handlers.memory.MemoryStateHandler'

    def test_checksum_persistence(self):
        """Make sure checksums are shared between threads."""
        checksum = '397fc6229a59429ee114441b780fe7a2'
        state_handler.set_checksum(0, checksum)
        getter = ChecksumGetter(0)
        getter.start()
        getter.join()
        self.assertEqual(getter.checksum, checksum)
        state_handler.clear_checksum(0)
        getter = ChecksumGetter(0)
        getter.start()
        getter.join()
        self.assertIsNone(getter.checksum)


class CacheHandlerTest(StateHandlerTestMixin, BaseModelDefinitionTestCase):
    handler_path = 'mutant.state.handlers.cache.CacheStateHandler'


@skipUnless(redis, 'This state handler requires redis to be installed.')
class PubsubHandlerTest(MemoryHandlerTest):
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
