import types

from django.db.models import base
from django.core.exceptions import ValidationError
from django.test.testcases import TestCase

from dynamodef.contrib.related.models import RelatedFieldDefinition
from dynamodef.db.fields import PythonObjectReferenceField
from dynamodef.models import FieldDefinitionBase
from dynamodef.tests.models.utils import BaseModelDefinitionTestCase

class ImportablePythonObjectFieldTest(BaseModelDefinitionTestCase):
    
    def setUp(self):
        super(ImportablePythonObjectFieldTest, self).setUp()
        self.base_field = PythonObjectReferenceField()
        self.null_field = PythonObjectReferenceField(null=True)
        self.model_base_field = PythonObjectReferenceField(allowed_types=(FieldDefinitionBase,))
        self.type_field = PythonObjectReferenceField(allowed_types=(types.TypeType,))
        self.module_field = PythonObjectReferenceField(allowed_types=(types.ModuleType,))
        self.tuple_field = PythonObjectReferenceField(allowed_types=(types.TupleType,))
        
    
    def test_nulltrue_allows_none_type(self):
        self.assertIsNone(self.null_field.to_python(None),
                          msg="PythonObjectReferenceField with null=True "
                              "should allow None types.")
        
        
    def test_allow_string_object_path(self):
        string_object_path = '.'.join(('dynamodef.contrib.related.models',
                                       'RelatedFieldDefinition'))
        self.assertEqual(RelatedFieldDefinition,
                         self.model_base_field.to_python(string_object_path).obj,
                         msg='Assigning a string path to an existing object with '
                             'an allowed type should return the correct object.')
        
    def test_allow_tuple_object_path(self):
        tuple_object_path = ('dynamodef.contrib.related.models',
                             'RelatedFieldDefinition')
        self.assertEqual(RelatedFieldDefinition,
                         self.model_base_field.to_python(tuple_object_path).obj,
                         msg='Assigning a tuple path to an existing object with '
                             'an allowed type should return the correct object.')
        
    def test_import_failures(self):
        # Inexistent module
        self.assertRaisesMessage(TypeError,
                                 "Specified arguments aren't a valid "
                                 "python object reference.",
                                 self.base_field.to_python, 'no-where')
        
        # Inexistent object in an existent module
        self.assertRaisesMessage(ImportError,
                                 'Cannot import name null from dynamodef',
                                 self.base_field.to_python, 'dynamodef.null')
        
    def test_module_type(self):
        self.assertEqual(base,
                         self.module_field.to_python('django.db.models.base').obj,
                         msg="Importing a module should work if its an allowed type")
        
    def test_allowed_types(self):
        self.assertRaisesMessage(ValidationError,
                                 "The object None's type 'NoneType' isn't allowed for this field.",
                                 self.base_field.to_python, None)
        
        self.assertRaisesMessage(ValidationError,
                                 "The object <class 'django.test.testcases.TestCase'>"
                                 "'s type 'type' isn't allowed for this field.",
                                 self.base_field.to_python, TestCase)
        
        self.assertEqual(TestCase, self.type_field.to_python(TestCase).obj,
                         msg="Assigning an allowed type should work")
        
        self.assertEqual(base, self.module_field.to_python(base).obj,
                         msg="Assigning an allowed type should work")

