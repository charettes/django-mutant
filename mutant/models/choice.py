
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.utils.translation import ugettext_lazy as _
from orderable.models import OrderableModel

from ..db.fields import (FieldDefinitionTypeField, PythonIdentifierField,
    LazilyTranslatedField)
from ..managers import ChoiceDefinitionManager
            
class ChoiceDefinition(OrderableModel):
    """
    An abstract model class representing a field_def choice
    """
    
    field_def_type = FieldDefinitionTypeField(verbose_name=_(u'field_def type'))
    group = LazilyTranslatedField(_(u'group'), blank=True, null=True)
    value = models.CharField(_(u'value'), max_length=255)
    label = LazilyTranslatedField(_(u'label'))
    
    objects = ChoiceDefinitionManager()
    
    class Meta(OrderableModel.Meta):
        abstract = True

# XXX: This might be a bit overkill, consider removing
class FieldDefinitionOptionChoice(ChoiceDefinition):
    """
    A Model to allow specifying choices for an option of a field definition.
     
    i. e. For FileFieldDefinition.upload_to.choices
     
    FieldDefinitionOptionChoice(field_def_type=file_field_definition_ct,
                                option='upload_to', order=0,
                                value='documents/%Y',
                                label='Yearly documents directory')
    """
    
    option_name = PythonIdentifierField(_(u'option'))
    
    class Meta:
        app_label = 'mutant'
        verbose_name = _(u'field_def option choice')
        verbose_name_plural = _(u'field_def option choices')
        unique_together = (('field_def_type', 'option_name', 'order'),
                           ('field_def_type', 'option_name', 'group', 'value'))
    
    @property
    def field_def_option(self):
        """
        Returns the option named after option_name of the field_type
        """
        field_def = self.field_def_type.model_class()
        return field_def._meta.get_field(self.option_name)

    def clean(self):
        try:
            self.field_def_option.to_python(self.value)
        except FieldDoesNotExist as e:
            # It's possible that the option_name isn't a valid option.
            # i. e. The Field subclass has no declared field_def named after it.
            msg = {'option_name': e.message}
            raise ValidationError(msg)
        except ValidationError as e:
            # The field definition couln't coerce the specified
            # string to a valid value
            msg = {'value': e.messages}
            raise ValidationError(msg)

def update_field_def_option_choices(instance, **kwargs):
    option_filter = {
        'field_def_type': instance.field_def_type,
        'option_name': instance.option_name
    }
    choices = tuple(FieldDefinitionOptionChoice.objects.filter(**option_filter).as_choices())
    instance.field_def_option._choices = choices or None

models.signals.post_save.connect(update_field_def_option_choices, FieldDefinitionOptionChoice)
models.signals.post_delete.connect(update_field_def_option_choices, FieldDefinitionOptionChoice)
