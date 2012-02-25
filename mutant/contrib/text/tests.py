
from django.db import connection
from django.db.utils import DatabaseError
from django.utils.unittest.case import skipUnless

from ...tests.models.utils import BaseModelDefinitionTestCase

from .models import CharFieldDefinition


class CharFieldDefinitionTest(BaseModelDefinitionTestCase):
    
    def setUp(self):
        super(CharFieldDefinitionTest, self).setUp()
        self.field = CharFieldDefinition.objects.create(model_def=self.model_def,
                                                        name='name',
                                                        max_length=255)
    
    def test_creation(self):
        Model = self.model_def.model_class()
        Model.objects.create(name='Raptor Jesus')
    
    @skipUnless(connection.settings_dict['ENGINE'] != 'django.db.backends.sqlite3',
                "Skipping because sqlite3 doesn't enforce CHAR length")
    def test_max_length(self):
        self.field.max_length = 24
        self.field.save()
        Model = self.model_def.model_class()
        with self.assertRaises(DatabaseError):
            Model.objects.create(name='Simon' * 5)