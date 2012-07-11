
from django.db.models import fields
from django.utils.translation import ugettext_lazy as _

from ...models import FieldDefinition


class _BooleanMeta:
    defined_field_category = _(u'Boolean')


class BooleanFieldDefinition(FieldDefinition):

    class Meta(_BooleanMeta):
        app_label = 'mutant'
        proxy = True
        defined_field_class = fields.BooleanField

class NullBooleanFieldDefinition(FieldDefinition):

    class Meta(_BooleanMeta):
        app_label = 'mutant'
        proxy = True
        defined_field_class = fields.NullBooleanField
