
from django.db import connection, connections, router
from django.test.testcases import _deferredSkip

from mutant.db.models import MutableModel
from mutant.models.model import ModelDefinition
from mutant.test.testcases import (ModelDefinitionDDLTestCase,
    VersionCompatMixinTestCase)


class BaseModelDefinitionTestCase(ModelDefinitionDDLTestCase,
                                  VersionCompatMixinTestCase):
    
    def setUp(self):
        self.model_def = ModelDefinition.objects.create(app_label='app',
                                                        object_name='Model')
        
    def assertTableExists(self, db, table_name):
        tables = connections[db].introspection.table_names()
        msg = "Table '%s.%s' doesn't exist, existing tables are %s"
        self.assertTrue(table_name in tables, msg % (db, table_name, tables))
        
    def assertTableDoesntExists(self, db, table_name):
        self.assertRaises(AssertionError, self.assertTableExists, db, table_name)
        
    def _table_columns_iterator(self, table_name):
        cursor = connection.cursor()
        description = connection.introspection.get_table_description(cursor, table_name)
        return (row[0] for row in description)
    
    def assertColumnExists(self, table_name, field_name):
        fields = self._table_columns_iterator(table_name)
        self.assertTrue(field_name in fields,
                        "Field '%(table)s.%(field)s' doesn't exist, '%(table)s'"
                        "'s fields are %(fields)s" % {'table': table_name,
                                                      'field': field_name,
                                                      'fields': fields})
        
    def assertColumnDoesntExists(self, table_name, field_name):
        self.assertRaises(AssertionError, self.assertColumnExists,
                          table_name, field_name)

def _get_mutant_model_db():
    # TODO: This should rely on syncdb instead
    return router.db_for_write(MutableModel)

def skipIfMutantModelDBFeature(feature, default=False):
    db = _get_mutant_model_db()
    return _deferredSkip(lambda: getattr(connections[db].features, feature, default),
                         "Database %s has feature %s" % (db, feature))

def skipUnlessMutantModelDBFeature(feature, default=True):
    db = _get_mutant_model_db()
    return _deferredSkip(lambda: not getattr(connections[db].features, feature, default),
                         "Database %s doesn't support feature %s" % (db, feature))
