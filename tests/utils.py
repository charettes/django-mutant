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
    @classmethod
    def setUpTestData(cls):
        model_def = ModelDefinition.objects.create(app_label='mutant', object_name='Model')
        cls.model_def_pk = model_def.pk

    def setUp(self):
        self.model_def = ModelDefinition.objects.get(pk=self.model_def_pk)

    @classmethod
    @contextmanager
    def assertChecksumChange(cls, model_def=None):
        if not model_def:
            model_def = ModelDefinition.objects.get(pk=cls.model_def_pk)
        checksum = model_def.model_class().checksum()
        yield
        if model_def.model_class().checksum() == checksum:
            raise AssertionError("Checksum of model %s should have changed." % model_def)

    @classmethod
    @contextmanager
    def assertChecksumDoesntChange(cls, model_def=None):
        if not model_def:
            model_def = ModelDefinition.objects.get(pk=cls.model_def_pk)
        try:
            with cls.assertChecksumChange(model_def):
                yield
        except AssertionError:
            pass
        else:
            model_class = model_def.model_class()
            raise AssertionError("Checksum of model %s shouldn't have changed." % model_class)

    def assertTableExists(self, db, table):
        tables = connections[db].introspection.table_names()
        msg = "Table '%s.%s' doesn't exist, existing tables are %s"
        self.assertTrue(table in tables, msg % (db, table, tables))

    def assertTableDoesntExists(self, db, table):
        tables = connections[db].introspection.table_names()
        msg = "Table '%s.%s' exists, existing tables are %s"
        self.assertFalse(table in tables, msg % (db, table, tables))

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
