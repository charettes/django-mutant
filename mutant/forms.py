
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import class_prepared
from django.forms.fields import ChoiceField
from django.forms.models import ModelChoiceField
from django.utils.text import capfirst

from mutant.common import choices_from_dict
from mutant.models.field import FieldDefinitionBase


class FieldDefinitionTypeField(ModelChoiceField):

    def __init__(self, *args, **kwargs):
        super(FieldDefinitionTypeField, self).__init__(ContentType.objects.all(),
                                                       *args, **kwargs)

    def _get_choices(self):
        if not hasattr(self.__class__, '_choices'):
            choices = []
            # Here we can't use ContentType.objects.get_for_models until
            # django's #18399 is fixed.
            for field_definition in FieldDefinitionBase._field_definitions.values():
                app_label = field_definition._meta.app_label
                model = field_definition._meta.object_name.lower()
                try:
                    ct = ContentType.objects.get_by_natural_key(app_label, model)
                except ContentType.DoesNotExist:
                    # Ignore stale ContentTypes
                    continue
                choices.append({
                    'value': ct.pk,
                    'label': capfirst(field_definition.get_field_description()),
                    'group': capfirst(field_definition.get_field_category()),
                })
            setattr(self.__class__, '_choices',
                    ((u"", self.empty_label),) + tuple(choices_from_dict(choices)))
        return self._choices

    choices = property(_get_choices, ChoiceField._set_choices)

def _clear_cached_choices(sender, **kwargs):
    if (isinstance(sender, FieldDefinitionBase) and
        hasattr(FieldDefinitionTypeField, '_choices')):
        delattr(FieldDefinitionTypeField, '_choices')

class_prepared.connect(_clear_cached_choices)
