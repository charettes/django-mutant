from __future__ import unicode_literals

import functools
import logging
import time
from threading import Thread
from unittest import skipUnless

from django.apps import apps
from django.test import SimpleTestCase
from django.utils.module_loading import import_string

from mutant.state import handler as state_handler
from mutant.state.handlers.pubsub import engines as pubsub_engines

from .utils import BaseModelDefinitionTestCase, LoggingTestMixin

try:
    import redis
except ImportError:
    redis = None


class StateHandlerTestMixin(object):
    def setUp(self):
        super(StateHandlerTestMixin, self).setUp()
        self.mutant_config = apps.get_app_config('mutant')
        self._state_handler = self.mutant_config.state_handler
        self.mutant_config.state_handler = import_string(self.handler_path)(**self.handler_options)

    def tearDown(self):
        self.mutant_config.state_handler = self._state_handler
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
    handler_options = {}

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
    handler_options = {}


class MockEngine(pubsub_engines.BaseEngine):
    def __init__(self, *args, **kwargs):
        self.published = []
        self._run = True
        super(MockEngine, self).__init__(*args, **kwargs)

    def run(self):
        self._initialize()
        while self._run:
            time.sleep(0.1)

    def publish(self, *args):
        self.published.append(args)

    def stop(self, timeout=None):
        self._run = False
        super(MockEngine, self).stop(timeout)


class PubsubHandlerTest(MemoryHandlerTest):
    handler_path = 'mutant.state.handlers.pubsub.PubSubStateHandler'
    handler_options = {'engine': ('tests.test_state.MockEngine', {})}

    def tearDown(self):
        state_handler.engine.stop()
        super(PubsubHandlerTest, self).tearDown()

    def test_flush(self):
        state_handler.set_checksum(0, '6818bab4da85a3a138cdfa35cfc7a64f')
        self.assertEqual(state_handler.get_checksum(0), '6818bab4da85a3a138cdfa35cfc7a64f')
        state_handler.flush()
        self.assertEqual(state_handler.checksums, {})
        self.assertNotEqual(state_handler.timestamps, {})

    def test_receive(self):
        state_handler.set_checksum(0, '6818bab4da85a3a138cdfa35cfc7a64f')
        timestamp = state_handler.timestamps[0]
        state_handler.receive(0, 'before', timestamp - 1)
        self.assertEqual(state_handler.get_checksum(0), '6818bab4da85a3a138cdfa35cfc7a64f')
        state_handler.receive(0, 'before', timestamp + 1)
        self.assertEqual(state_handler.get_checksum(0), 'before')
        state_handler.receive(0, None, timestamp + 1)
        self.assertIsNone(state_handler.get_checksum(0))


@skipUnless(redis, 'This state handler requires redis to be installed.')
class RedisPubSubHandlerEngineTests(LoggingTestMixin, SimpleTestCase):
    class TestRedis(pubsub_engines.Redis):
        initialized = False
        exception = redis.RedisError

        def _run(self):
            self._run = functools.partial(pubsub_engines.Redis._run, self)
            raise self.exception

    def test_timeout_reconnects(self):
        messages = []

        def initialize():
            engine.initialized = True

        def collect_messages(*args):
            messages.append(args)

        engine = self.TestRedis(initialize, collect_messages, channel=str(self))
        engine.exception = redis.TimeoutError
        with self.record(pubsub_engines.logger) as records:
            engine.start()
            while not engine.ready:
                time.sleep(0.1)
        self.assertTrue(engine.initialized)
        self.assertEqual(len(records), 3)
        first_record, second_record, third_record = records
        self.assertEqual(first_record.levelno, logging.WARNING)
        self.assertEqual(first_record.msg, 'Unexpected connection timeout.')
        self.assertEqual(second_record.levelno, logging.INFO)
        self.assertEqual(second_record.msg, 'Attempting to reconnect.')
        self.assertEqual(third_record.levelno, logging.INFO)
        self.assertEqual(third_record.msg, 'Successfully reconnected.')
        engine.publish('foo', 'bar')
        while len(messages) == 0:
            time.sleep(0.1)
        self.assertEqual(messages, [('foo', 'bar')])
        engine.stop()

    def test_disconnect_reconnects(self):
        messages = []

        def initialize():
            engine.initialized = True

        def collect_messages(*args):
            messages.append(args)

        engine = self.TestRedis(initialize, collect_messages, channel=str(self))
        engine.exception = redis.ConnectionError
        with self.record(pubsub_engines.logger) as records:
            engine.start()
            while not engine.ready:
                time.sleep(0.1)
        self.assertTrue(engine.initialized)
        self.assertEqual(len(records), 3)
        first_record, second_record, third_record = records
        self.assertEqual(first_record.levelno, logging.WARNING)
        self.assertEqual(first_record.msg, 'Connection error.')
        self.assertEqual(second_record.levelno, logging.INFO)
        self.assertEqual(second_record.msg, 'Attempting to reconnect.')
        self.assertEqual(third_record.levelno, logging.INFO)
        self.assertEqual(third_record.msg, 'Successfully reconnected.')
        engine.publish('foo', 'bar')
        while len(messages) == 0:
            time.sleep(0.1)
        self.assertEqual(messages, [('foo', 'bar')])
        engine.stop()
