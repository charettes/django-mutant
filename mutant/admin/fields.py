
from django.contrib.contenttypes.models import ContentType
from django.forms.models import ModelChoiceField
from django.utils.text import capfirst

from mutant.common import choices_from_dict
from mutant.models.field import FieldDefinitionBase

class FieldDefinitionTypeField(ModelChoiceField):
    
    def __init__(self, *args, **kwargs):
        super(FieldDefinitionTypeField, self).__init__(*args, **kwargs)
        fcs = FieldDefinitionBase._field_classes
        choices = ({'value': (ContentType.objects.filter(app_label=fdc._meta.app_label,
                                                        model=fdc._meta.object_name.lower())
                                        .values_list('id', flat=True)[0]),
                    'label': capfirst(fdc.get_field_description()),
                    'group': capfirst(fdc._meta.defined_field_category)}
                        for fc, fdc in fcs.iteritems())
        self._choices = ((u"", self.empty_label),) + tuple(choices_from_dict(choices))