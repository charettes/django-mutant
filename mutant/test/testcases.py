import re

import django
from django.contrib.contenttypes.models import ContentType
from django.db import connections
from django.test.testcases import TestCase
from south.db import dbs as south_dbs

from ..models.model import ModelDefinition


def connections_support_ddl_transactions():
    """
    Returns True if all connections support ddl transactions
    """
    return all(south_dbs[name].has_ddl_transactions for name in connections)

class DDLTestCase(TestCase):
    """
    A class that behaves like TestCase if all connections support ddl
    transactions or like TransactionTestCase if it's not the case.
    """
    
    def _fixture_setup(self):
        if not connections_support_ddl_transactions():
            return super(TestCase, self)._fixture_setup()
        else:
            return super(DDLTestCase, self)._fixture_setup()
        
    def _fixture_teardown(self):
        if not connections_support_ddl_transactions():
            return super(TestCase, self)._fixture_teardown()
        else:
            return super(DDLTestCase, self)._fixture_teardown()
        
class ModelDefinitionDDLTestCase(DDLTestCase):
    
    def tearDown(self):
        if not connections_support_ddl_transactions():
            # We must delete the ModelDefinition tables by ourself since
            # they won't be removed by a rollback.
            for md in ModelDefinition.objects.all():
                md.delete()
        ContentType.objects.clear_cache()
        
class VersionCompatMixinTestCase(TestCase):
    
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
        