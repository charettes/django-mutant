from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _
from djangotoolbox import fields
from picklefield.fields import PickledObjectField

from ...hacks import patch_db_field_compare
from ...models import FieldDefinition, FieldDefinitionManager


# Since we use a pickled field that might contain a Field instance
# we must make sure their cmp methods works correctly.
patch_db_field_compare()

class _NonRelMeta:
    defined_field_category = _('Nonrel')


class AbstractIterableFieldDefinition(FieldDefinition):
    item_field = PickledObjectField(_('item field'), blank=True, null=True)

    objects = FieldDefinitionManager()

    class Meta(_NonRelMeta):
        abstract = True
        defined_field_options = ('item_field',)


class DictFieldDefinition(AbstractIterableFieldDefinition):
    class Meta(_NonRelMeta):
        app_label = 'mutant'
        defined_field_class = fields.DictField
        defined_field_description = _('Dict')


class ListFieldDefinition(AbstractIterableFieldDefinition):
    ordering = PickledObjectField(_('ordering'), blank=True, null=True)

    class Meta(_NonRelMeta):
        app_label = 'mutant'
        defined_field_class = fields.ListField
        defined_field_options = ('ordering',)
        defined_field_description = _('List')


# This class isn't working correctly on pymongo
# It doesn't know how to encode set... see testcases
# InvalidDocument: Cannot encode object: set(['A', 'Y', 'C', 'M'])
class SetFieldDefinition(AbstractIterableFieldDefinition):
    class Meta(_NonRelMeta):
        app_label = 'mutant'
        defined_field_class = fields.SetField
        defined_field_description = _('Set')


class BlobFieldDefinition(FieldDefinition):
    class Meta(_NonRelMeta):
        app_label = 'mutant'
        proxy = True
        defined_field_class = fields.BlobField
        defined_field_description = _('Blob')


class EmbeddedModelFieldDefinition(FieldDefinition):
    model = models.ForeignKey(ContentType, verbose_name=_('model'),
                              related_name='+', blank=True, null=True)

    objects = FieldDefinitionManager()

    class Meta(_NonRelMeta):
        app_label = 'mutant'
        defined_field_class = fields.EmbeddedModelField
        defined_field_description = _('Embedded model')

    def get_field_options(self, **overrides):
        options = super(EmbeddedModelFieldDefinition, self).get_field_options(**overrides)
        if self.model:
            options['model'] = self.model.model_class()
        return options
