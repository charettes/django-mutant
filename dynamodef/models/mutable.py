
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.fields import FieldDoesNotExist

from dynamodef.models import (FieldDefinition, ModelDefinition, MixinDefinition,
    ModelBaseDefinition)
from django.core.exceptions import ImproperlyConfigured


class MutableModelBase(models.base.ModelBase):
    """
    Metaclass for all mutable models.
    """
    def __new__(cls, name, bases, attrs):
        model = super(MutableModelBase, cls).__new__(cls, name, bases, attrs)
        model_meta = model._meta
        
        # There's nothing to do with abstract or unique models
        if model_meta.abstract or model_meta.unique:
            return model
        
        app_label, object_name = model_meta.app_label, model_meta.object_name
        
        try:
            model_def = ModelDefinition.objects.get(app_label=app_label,
                                                    object_name=object_name)
        except ModelDefinition.DoesNotExist:
            pass
        else:
            # The model definition already exists.
            # We make sure the non-mutable fields (the ones defined on the model)
            # exist on the definition and that they have the same defined options
            for field in model_meta.fields:
                try:
                    field_def = model_def.fields.get(name=field.name)
                except FieldDefinition.DoesNotExist:
                    # TODO: Throw an error explaining a non-mutable field is missing
                    # from the definition if we're not in "schema-migration" mode
                    raise ImproperlyConfigured("A non mutable field is missing some")
                else:
                    if field_def.editable:
                        #TODO: Raise a warning specifying this could lead to a field
                        # removal of alteration of a non-mutable field
                        pass
                    for opt, value in field_def.get_field_options().iteritems():
                        if getattr(field, opt) != value:
                            # TODO: Throw an exception telling the user a "frozen"
                            # field definition doesn't match the one provided
                            raise ImproperlyConfigured()
            return model_def.defined_object

        # The model
        for field in model_meta.fields:
            field_def_klass = FieldDefinition
            
            field_def = field_def_klass(model_def=model_def,
                                        name=field.name,
                                        editable=False)

            for opt in field_def._meta.defined_field_options:
                setattr(field_def, opt, getattr(field, opt))
            field_def.save()
        
        #TODO: Find a way to avoid flushing all bases away
        has_defined_model_base = False
        base_defs = []
        model_def.bases.clear()
        for base in bases:
            if issubclass(base, models.Model):
                if not base == models.Model:
                    base_ct = ContentType.objects.get_for_model(base)
                    base_def = ModelBaseDefinition(model_def=model_def,
                                                   content_type=base_ct)
                    if issubclass(base, ModelDefinition.DefinedModel):
                        has_defined_model_base = True
            else:
                base_def = MixinDefinition(model_def=model_def,
                                           reference=base)
            base_def.order = len(base_defs)
            base_def.save()
            base_defs.append(base_def)
        model_def.base_defs = base_defs
        
        if not has_defined_model_base:
            bases += (ModelDefinition.DefinedModel,)
        
        # Make sure to clear the model cache
        del models.loading.model_cache.app_models[app_label][object_name]
        return super(MutableModelBase, cls).__new__(cls, name, bases, attrs)
        