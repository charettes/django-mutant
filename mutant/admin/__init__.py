
from django.contrib import admin
from django.forms.widgets import TextInput

from mutant.admin.fields import FieldDefinitionTypeField
from mutant.models.field import FieldDefinition
from mutant.models.model import ModelDefinition, UniqueTogetherDefinition

class UniqueTogetherDefinitionInline(admin.TabularInline):
    
    model = UniqueTogetherDefinition

class FieldDefinitionInline(admin.StackedInline):
    
    model = FieldDefinition
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name in ('verbose_name', 'help_text'):
            kwargs['widget'] = TextInput
        return super(FieldDefinitionInline, self).formfield_for_dbfield(db_field, **kwargs)
    
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'field_type':
            kwargs['form_class'] = FieldDefinitionTypeField
        sup = super(FieldDefinitionInline, self)
        return sup.formfield_for_foreignkey(db_field, request, **kwargs)

class ModelDefinitionAdmin(admin.ModelAdmin):
    
    list_display = ('app_label', 'object_name')
    
    inlines = (FieldDefinitionInline, UniqueTogetherDefinitionInline,)
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name in ('verbose_name', 'verbose_name_plural'):
            kwargs['widget'] = TextInput
        return super(ModelDefinitionAdmin, self).formfield_for_dbfield(db_field, **kwargs)
    
admin.site.register(ModelDefinition, ModelDefinitionAdmin)
