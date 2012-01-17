
from django.db.models import fields

from dynamodef.models import FieldDefinition

class FieldDefinitionProxy(FieldDefinition):
    
    class Meta:
        proxy = True
#        defined_field_class = fields.CharField
        
class FieldDefinitionSubclass(FieldDefinition):
    
    option = fields.BooleanField()
    fk = fields.related.ForeignKey(FieldDefinitionProxy, related_name='fks')
    m2m = fields.related.ManyToManyField(FieldDefinitionProxy, related_name='m2ms')

    class Meta:
#        defined_field_class = fields.CharField
        defined_field_options = ('option', 'fk', 'm2m')
        
class AbstractFieldDefinition(FieldDefinition):
    
    useless_option = fields.BooleanField()
    
    class Meta:
        abstract = True
        defined_field_options = ('useless_option',)
        
class AbstractFieldDefinitionSubclass(FieldDefinition):
    
    non_option_field = fields.BooleanField()
    other_option = fields.BooleanField()
    
    class Meta:
        abstract = True
        defined_field_options = ('other_option',)

#class MutipleInheritanceFieldDefinition(AbstractFieldDefinitionSubclass,
#                                        FieldDefinitionSubclass):
#    pass
