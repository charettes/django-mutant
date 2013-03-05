from __future__ import unicode_literals

from django.core.signals import request_started
from django.db import reset_queries


try:
    from django.test.utils import CaptureQueriesContext
except ImportError:
    # TODO: Remove when support for Django < 1.6 is dropped
    class CaptureQueriesContext(object):
        """
        Context manager that captures queries executed by the specified connection.
        """
        def __init__(self, connection):
            self.connection = connection

        def __iter__(self):
            return iter(self.captured_queries)

        def __getitem__(self, index):
            return self.captured_queries[index]

        def __len__(self):
            return len(self.captured_queries)

        @property
        def captured_queries(self):
            return self.connection.queries[self.initial_queries:self.final_queries]

        def __enter__(self):
            self.use_debug_cursor = self.connection.use_debug_cursor
            self.connection.use_debug_cursor = True
            self.initial_queries = len(self.connection.queries)
            self.final_queries = None
            request_started.disconnect(reset_queries)
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            self.connection.use_debug_cursor = self.use_debug_cursor
            request_started.connect(reset_queries)
            if exc_type is not None:
                return
            self.final_queries = len(self.connection.queries)
