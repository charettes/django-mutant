from __future__ import unicode_literals

from django.db.models import fields
from django.utils.translation import ugettext_lazy as _

from ...models.field import FieldDefinition


class _BooleanMeta:
    defined_field_category = _('Boolean')


class BooleanFieldDefinition(FieldDefinition):
    class Meta(_BooleanMeta):
        app_label = 'boolean'
        proxy = True
        defined_field_class = fields.BooleanField


class NullBooleanFieldDefinition(FieldDefinition):
    class Meta(_BooleanMeta):
        app_label = 'boolean'
        proxy = True
        defined_field_class = fields.NullBooleanField
