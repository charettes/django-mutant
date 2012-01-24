
from dynamodef.contrib.text.models import CharFieldDefinition
from dynamodef.tests.models.utils import BaseModelDefinitionTestCase


class CharFieldDefinitionTest(BaseModelDefinitionTestCase):
    
    def test_creation(self):
        cf = CharFieldDefinition.objects.create(model_def=self.model_def,
                                                name='name', max_length=255)
        Model = self.model_def.model_class()
        Model.objects.create(name='Raptor Jesus')