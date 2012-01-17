
from dynamodef.contrib.related.models import ForeignKeyDefinition
from dynamodef.models.model import ModelDefinition
from dynamodef.tests.models.utils import BaseModelDefinitionTestCase
from django.core.exceptions import ValidationError

__all__ = ('ForeignKeyDefinitionTest',)

class ForeignKeyDefinitionTest(BaseModelDefinitionTestCase):
    
    def test_simple_foreign_key(self):
        first_model_def = self.model_def
        second_model_def = ModelDefinition.objects.create(app_label='app',
                                                          object_name='SecondModel')
        FirstModel = first_model_def.defined_object
        SecondModel = second_model_def.defined_object
        ForeignKeyDefinition.objects.create(model_def=first_model_def,
                                            name='second', null=True,
                                            to=second_model_def.model_ct)
        
        second = SecondModel.objects.create()
        first = FirstModel.objects.create(second=second)
        
        ForeignKeyDefinition.objects.create(model_def=second_model_def,
                                            name='first', null=True,
                                            to=first_model_def.model_ct)
        
        second.first = first
        self.assertRaisesMessage(ValidationError,
                                 'Cannot save an obsolete model', second.save)
        
        second = SecondModel.objects.get()
        second.first = first
        second.save()
        
        second_model_def.delete()
        
    def test_recursive_relationship(self):
        fk = ForeignKeyDefinition.objects.create(model_def=self.model_def,
                                                 name='f1', null=True, blank=True,
                                                 to=self.model_def.model_ct)
        self.assertTrue(fk.is_recursive_relationship)
        
        Model = self.model_def.defined_object
        self.assertTrue(Model._meta.get_field('f1').rel.to == Model)

        obj1 = Model.objects.create()
        obj2 = Model.objects.create(f1=obj1)
        obj1.f1 = obj2
        obj1.save()
