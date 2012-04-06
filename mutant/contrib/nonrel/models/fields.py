
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _
from djangotoolbox import fields
from picklefield.fields import PickledObjectField

from ....hacks import patch_db_field_compare
from ....models import FieldDefinition


# Since we use a pickled field that might contain a Field instance
# we must make sure their cmp methods works correctly.
patch_db_field_compare()

class AbstractIterableFieldDefinition(FieldDefinition):
    
    item_field = PickledObjectField(_(u'item field'), blank=True, null=True)
    
    class Meta:
        abstract = True
        defined_field_options = ('item_field',)
        defined_field_category = _(u'nonrel')

class DictFieldDefinition(AbstractIterableFieldDefinition):
    
    class Meta:
        app_label = 'mutant'
        verbose_name = _(u'dict field')
        verbose_name_plural = _(u'dict fields')
        defined_field_class = fields.DictField

class ListFieldDefinition(AbstractIterableFieldDefinition):
    
    ordering = PickledObjectField(_(u'ordering'), blank=True, null=True)
    
    class Meta:
        app_label = 'mutant'
        verbose_name = _(u'list field')
        verbose_name_plural = _(u'list fields')
        defined_field_class = fields.ListField
        defined_field_options = ('ordering',)

# This class isn't working correctly on pymongo
# It doesn't know how to encode set... see testcases
# InvalidDocument: Cannot encode object: set(['A', 'Y', 'C', 'M'])
class SetFieldDefinition(AbstractIterableFieldDefinition):
    
    class Meta:
        app_label = 'mutant'
        verbose_name = _(u'set field')
        verbose_name_plural = _(u'set fields')
        defined_field_class = fields.SetField
        
class BlobFieldDefinition(FieldDefinition):
    
    class Meta:
        app_label = 'mutant'
        proxy = True
        verbose_name = _(u'blob field')
        verbose_name_plural = _(u'blob fields')
        defined_field_class = fields.BlobField
        defined_field_category = _(u'nonrel')
        
class EmbeddedModelFieldDefinition(FieldDefinition):
    
    model = models.ForeignKey(ContentType, verbose_name=_(u'model'),
                              related_name='+', blank=True, null=True)
    
    class Meta:
        app_label = 'mutant'
        verbose_name = _(u'embedded model field')
        verbose_name_plural = _(u'embedded model fields')
        defined_field_class = fields.EmbeddedModelField
        defined_field_category = _(u'nonrel')
    
    def get_field_options(self):
        options = super(EmbeddedModelFieldDefinition, self).get_field_options()
        if self.model:
            options['model'] = self.model.model_class()
        return options
    