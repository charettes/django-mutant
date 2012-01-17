import sqlite3

from django.db import connection, transaction
from django.db.utils import DatabaseError, IntegrityError

from dynamodef.contrib.text.models import CharFieldDefinition
from dynamodef.tests.models.utils import BaseModelDefinitionTestCase

class FieldDefinitionInheritanceTest(BaseModelDefinitionTestCase):
    
    @transaction.autocommit
    def test_proxy_inheritance(self):
        obj = CharFieldDefinition.objects.create(name='caca',
                                                  max_length=25,
                                                  model_def=self.model_def)
        save_obj = self.model_def.fielddefinitions.select_subclasses().get()
        self.assertEqual(obj, save_obj)
        
        Model = self.model_def.defined_object
        Model.objects.create(caca="NO WAY")

class FieldDefinitionManipulation(BaseModelDefinitionTestCase):
    
    @transaction.autocommit
    def test_field_renaming(self):
        field = CharFieldDefinition.objects.create(name='name',
                                                   max_length=25,
                                                   model_def=self.model_def)
        
        field.name = 'first_name'
        field.save()
        
        Model = self.model_def.defined_object
        msg = "'name' is an invalid keyword argument for this function"
        self.assertRaisesMessage(TypeError, msg,
                                 Model.objects.create, name="Simon")
        
        Model.objects.create(first_name="Julien")
    
    def test_field_alteration(self):
        with transaction.commit_on_success():
            field = CharFieldDefinition.objects.create(name='name',
                                                       max_length=24,
                                                       model_def=self.model_def)
            
        if not isinstance(connection.connection,
                          sqlite3.Connection):
            # sqlite3 doesn't enforce char length
            with transaction.commit_on_success():
                Model = self.model_def.defined_object
                with self.assertRaises(DatabaseError):
                    Model.objects.create(name='Simon' * 5)
        
        with transaction.commit_on_success():
            field.max_length = 25
            field.save()
            Model = self.model_def.defined_object
            Model.objects.create(name='Simon' * 5)
        
        with transaction.commit_on_success():
            field.unique = True
            field.save()
        
        with transaction.commit_on_success():
            Model = self.model_def.defined_object
            Model.objects.create(name='Simon')
            with self.assertRaises(IntegrityError):
                Model.objects.create(name='Simon')
