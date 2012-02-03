import re

import django
from django.db import connection, transaction
from django.test.testcases import TransactionTestCase
from south.db import db as south_api

from mutant.models.model import ModelDefinition

class BaseModelDefinitionTestCase(TransactionTestCase):
    
    def setUp(self):
        with transaction.commit_on_success():
            self.model_def = ModelDefinition.objects.create(app_label='app',
                                                            object_name='Model')
    
    # Django < 1.4 doesn't have assertIsIntance and `ordered` kwarg for assertQuerysetEqual
    if django.VERSION[0] == 1 and django.VERSION[1] < 4:
        def assertRaisesMessage(self, expected_exception, expected_message,
                                callable_obj=None, *args, **kwargs):
            return self.assertRaisesRegexp(expected_exception,
                    re.escape(expected_message), callable_obj, *args, **kwargs)
            
        def assertQuerysetEqual(self, qs, values, transform=repr, ordered=True):
            if not ordered:
                return self.assertEqual(set(map(transform, qs)), set(values))
            return self.assertEqual(map(transform, qs), values)
    
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
    
    def tearDown(self):
        try: # Try removing the model
            with transaction.commit_on_success():
                for md in ModelDefinition.objects.all():
                    md.delete()
        except Exception:
            raise
            # If it fails we still want to remove the table in order to avoid
            # interfering with other tests
            try:
                with transaction.commit_on_success():
                    south_api.delete_table(self.model_def.model_class()._meta.db_table) #@UndefinedVariable
            except Exception:
                pass
            # After trying our best to avoid tests collisions we re-raise the
            # actual exception
            raise
