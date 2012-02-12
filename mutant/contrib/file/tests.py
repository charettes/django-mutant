import os
import sys

from mutant.tests.models.utils import BaseModelDefinitionTestCase

from .models import FilePathFieldDefinition

__all__ = ('FilePathFieldDefinitionTest',)

PACKAGE_PATH = os.path.dirname(sys.modules[__name__].__file__)
MODULE_PATH = os.path.abspath(sys.modules[__name__].__file__)

class FilePathFieldDefinitionTest(BaseModelDefinitionTestCase):
    
    def setUp(self):
        super(FilePathFieldDefinitionTest, self).setUp()
        self.field = FilePathFieldDefinition.objects.create(model_def=self.model_def,
                                                            name='file_path',
                                                            path=PACKAGE_PATH)
    
    def test_creation(self):
        Model = self.model_def.model_class()
        Model.objects.create(file_path=MODULE_PATH)
        
    def test_formfield(self):
        self.field.match = r'\.pyc?$'
        self.field.save()
        formfield = self.field.field_instance().formfield()
        self.assertTrue(formfield.valid_value(MODULE_PATH))
        invalid_path = os.path.abspath(sys.modules[BaseModelDefinitionTestCase.__module__].__file__)
        self.assertFalse(formfield.valid_value(invalid_path))
        