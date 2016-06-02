from __future__ import unicode_literals

import logging
from contextlib import contextmanager

from django.db import connections

from mutant.models.model import ModelDefinition
from mutant.test.testcases import ModelDefinitionDDLTestCase
from mutant.utils import allow_migrate


def table_columns_iterator(db, table_name):
    connection = connections[db]
    cursor = connection.cursor()
    description = connection.introspection.get_table_description(cursor, table_name)
    return (row[0] for row in description)


class BaseModelDefinitionTestCase(ModelDefinitionDDLTestCase):
    def setUp(self):
        self.model_def = ModelDefinition.objects.create(
            app_label='mutant',
            object_name='Model'
        )

    @contextmanager
    def assertChecksumChange(self, model_def=None):
        model_def = model_def or self.model_def
        checksum = model_def.model_class().checksum()
        yield
        self.assertNotEqual(
            model_def.model_class().checksum(), checksum,
            "Checksum of model %s should have changed." % model_def
        )

    @contextmanager
    def assertChecksumDoesntChange(self, model_def=None):
        try:
            with self.assertChecksumChange(model_def):
                yield
        except AssertionError:
            pass
        else:
            model_class = (model_def or self.model_def).model_class()
            self.fail(
                "Checksum of model %s shouldn't have changed." % model_class
            )

    def assertTableExists(self, db, table):
        tables = connections[db].introspection.table_names()
        msg = "Table '%s.%s' doesn't exist, existing tables are %s"
        self.assertTrue(table in tables, msg % (db, table, tables))

    def assertTableDoesntExists(self, db, table):
        self.assertRaises(AssertionError, self.assertTableExists, db, table)

    def assertModelTablesExist(self, model):
        table = model._meta.db_table
        for db in allow_migrate(model):
            self.assertTableExists(db, table)

    def assertModelTablesDontExist(self, model):
        table = model._meta.db_table
        for db in allow_migrate(model):
            self.assertTableDoesntExists(db, table)

    def assertColumnExists(self, db, table, column):
        columns = tuple(table_columns_iterator(db, table))
        data = {
            'db': db,
            'table': table,
            'column': column,
            'columns': columns
        }
        self.assertIn(column, columns,
                      "Column '%(db)s.%(table)s.%(column)s' doesn't exist, "
                      "%(db)s.'%(table)s's columns are %(columns)s" % data)

    def assertColumnDoesntExists(self, db, table, column):
        self.assertRaises(
            AssertionError, self.assertColumnExists, db, table, column
        )

    def assertModelTablesColumnExists(self, model, column):
        table = model._meta.db_table
        for db in allow_migrate(model):
            self.assertColumnExists(db, table, column)

    def assertModelTablesColumnDoesntExists(self, model, column):
        table = model._meta.db_table
        for db in allow_migrate(model):
            self.assertColumnDoesntExists(db, table, column)


class Recorder(logging.Handler):
    """Logging handler that stores emitted records."""

    def __init__(self):
        super(Recorder, self).__init__()
        self.emitted_records = []

    def emit(self, record):
        self.emitted_records.append(record)


class LoggingTestMixin(object):
    @contextmanager
    def handle(self, logger, handler, level=logging.INFO):
        """Context manager that attach a handler to a logger."""
        original_level = logger.level
        logger.setLevel(level)
        logger.addHandler(handler)
        try:
            yield
        finally:
            logger.setLevel(original_level)
            logger.removeHandler(handler)

    @contextmanager
    def record(self, logger, level=logging.INFO):
        """Context manager that capture the logger emitted records."""
        recorder = Recorder()
        with self.handle(logger, recorder, level):
            yield recorder.emitted_records
