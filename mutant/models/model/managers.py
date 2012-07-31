from __future__ import unicode_literals

from django.db import models


class ModelDefinitionManager(models.Manager):
    use_for_related_fields = True

    def get_by_natural_key(self, app_label, model):
        return self.get(app_label=app_label, model=model)

    def create(self, bases=(), fields=(), **kwargs):
        obj = self.model(**kwargs)
        extra_fields = []
        delayed_save = []
        for base in bases:
            assert base.pk is None, 'Cannot associate already existing BaseDefinition'
            extra_fields.extend([(f.get_attname_column()[1], f)
                                 for f in base.get_declared_fields()])
            base._state._add_columns = False
            delayed_save.append(base)
        for field in fields:
            assert field.pk is None, 'Cannot associate already existing FieldDefinition'
            field_instance = field._south_ready_field_instance()
            extra_fields.append((field_instance.get_attname_column()[1], field_instance))
            field._state._add_column = False
            delayed_save.append(field)
        # Add those fields to the instance state to be retrieved later
        obj._state._create_extra_fields = extra_fields
        obj._state._create_delayed_save = delayed_save
        # Force for write
        self._for_write = True
        obj.save(force_insert=True, using=self.db)
        return obj
