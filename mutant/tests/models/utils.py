
from django.db import connection

from mutant.models.model import ModelDefinition
from mutant.test.testcases import (ModelDefinitionDDLTestCase,
    VersionCompatMixinTestCase)


class BaseModelDefinitionTestCase(ModelDefinitionDDLTestCase,
                                  VersionCompatMixinTestCase):
    
    def setUp(self):
        self.model_def = ModelDefinition.objects.create(app_label='app',
                                                        object_name='Model')
    
    def _table_list(self):
        cursor = connection.cursor()
        return connection.introspection.get_table_list(cursor)
    
    def assertTableExists(self, table_name):
        tables = self._table_list()
        self.assertTrue(table_name in tables,
                        "Table '%s' doesn't exist, existing tables are %s" % (table_name,
                                                                              tables))
        
    def assertTableDoesntExists(self, table_name):
        self.assertRaises(AssertionError, self.assertTableExists, table_name)
        
    def _table_fields_iterator(self, table_name):
        cursor = connection.cursor()
        description = connection.introspection.get_table_description(cursor, 
                                                                     table_name)
        return (row[0] for row in description)
    
    def assertFieldExists(self, table_name, field_name):
        fields = self._table_fields_iterator(table_name)
        self.assertTrue(field_name in fields,
                        "Field '%(table)s.%(field)s' doesn't exist, '%(table)s'"
                        "'s fields are %(fields)s" % {'table': table_name,
                                                      'field': field_name,
                                                      'fields': fields})
        
    def assertFieldDoesntExists(self, table_name, field_name):
        self.assertRaises(AssertionError, self.assertFieldExists,
                          table_name, field_name)
