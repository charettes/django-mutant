from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from mutant.models import FieldDefinition
from mutant.db.fields import FieldDefinitionTypeField


class CustomFieldDefinition(FieldDefinition):
    class Meta:
        app_label = 'mutant'
        defined_field_category = _('Custom category')
        defined_field_description = _('Custom description')


class FieldDefinitionModel(models.Model):
    field_type = FieldDefinitionTypeField()

    class Meta:
        app_label = 'mutant'
