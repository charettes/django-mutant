
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from mutant.contrib.related.models import (ForeignKeyDefinition,
    ManyToManyFieldDefinition)
from mutant.models.model import ModelDefinition
from mutant.tests.models.utils import BaseModelDefinitionTestCase

__all__ = ('ForeignKeyDefinitionTest', 'ManyToManyFieldDefinitionTest')

class ForeignKeyDefinitionTest(BaseModelDefinitionTestCase):
    
    def test_simple_foreign_key_between_mutable_models(self):
        first_model_def = self.model_def
        second_model_def = ModelDefinition.objects.create(app_label='app',
                                                          object_name='SecondModel')
        FirstModel = first_model_def.model_class()
        SecondModel = second_model_def.model_class()
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
        
        Model = self.model_def.model_class()
        self.assertEqual(Model._meta.get_field('f1').rel.to, Model)

        obj1 = Model.objects.create()
        obj2 = Model.objects.create(f1=obj1)
        obj1.f1 = obj2
        obj1.save()
        
class ManyToManyFieldDefinitionTest(BaseModelDefinitionTestCase):
    
    def test_symmetrical(self):
        m2m = ManyToManyFieldDefinition(model_def=self.model_def, name='objs')
        ct_ct = ContentType.objects.get_for_model(ContentType)
        m2m.to = ct_ct
        
        with self.assertRaises(ValidationError):
            m2m.symmetrical = True
            m2m.clean()
            
        with self.assertRaises(ValidationError):
            m2m.symmetrical = False
            m2m.clean()
        
        m2m.to = self.model_def.model_ct
        
        # Make sure `symetrical=True` works
#        m2m.symmetrical = True
#        m2m.clean()
#        m2m.save()
#        
#        Model = self.model_def.model_class()
#        first_object = Model.objects.create()
#        second_object = Model.objects.create()
#        
#        first_object.objs.add(second_object)
#        self.assertIn(first_object, second_object.objs.all())
        
        # Makes sure non-symmetrical works
        m2m.symmetrical = False
        m2m.clean()
        m2m.save()
        
        Model = self.model_def.model_class()
        first_object = Model.objects.create()
        second_object = Model.objects.create()
        
        first_object.objs.add(second_object)
        self.assertNotIn(first_object, second_object.objs.all())
        
        first_object.objs.clear()
