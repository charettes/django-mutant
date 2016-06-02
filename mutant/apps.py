from __future__ import unicode_literals

from django.apps import AppConfig
from django.db import models
from django.utils.module_loading import import_string

from . import settings


class MutantConfig(AppConfig):
    name = 'mutant'

    def ready(self):
        self.state_handler = import_string(settings.STATE_HANDLER)()

        from . import management

        ModelDefinition = self.get_model('ModelDefinition')
        models.signals.post_save.connect(
            management.model_definition_post_save,
            sender=ModelDefinition,
            dispatch_uid='mutant.management.model_definition_post_save',
        )
        models.signals.pre_delete.connect(
            management.model_definition_pre_delete,
            sender=ModelDefinition,
            dispatch_uid='mutant.management.model_definition_pre_delete',
        )
        models.signals.post_delete.connect(
            management.model_definition_post_delete,
            sender=ModelDefinition,
            dispatch_uid='mutant.management.model_definition_post_delete',
        )

        BaseDefinition = self.get_model('BaseDefinition')
        models.signals.post_save.connect(
            management.base_definition_post_save,
            sender=BaseDefinition,
            dispatch_uid='mutant.management.base_definition_post_save',
        )
        models.signals.pre_delete.connect(
            management.base_definition_pre_delete,
            sender=BaseDefinition,
            dispatch_uid='mutant.management.base_definition_pre_delete',
        )
        models.signals.post_delete.connect(
            management.base_definition_post_delete,
            sender=BaseDefinition,
            dispatch_uid='mutant.management.base_definition_post_delete',
        )

        UniqueTogetherDefinition = self.get_model('UniqueTogetherDefinition')
        models.signals.m2m_changed.connect(
            management.unique_together_field_defs_changed,
            sender=UniqueTogetherDefinition.field_defs.through,
            dispatch_uid='mutant.management.unique_together_field_defs_changed',
        )

        FieldDefinition = self.get_model('FieldDefinition')
        models.signals.post_save.connect(
            management.raw_field_definition_proxy_post_save,
            sender=FieldDefinition,
            dispatch_uid='mutant.management.raw_field_definition_proxy_post_save',
        )
        models.signals.pre_delete.connect(
            management.field_definition_pre_delete,
            sender=FieldDefinition,
            dispatch_uid='mutant.management.field_definition_pre_delete',
        )
        models.signals.post_delete.connect(
            management.field_definition_post_delete,
            sender=FieldDefinition,
            dispatch_uid='mutant.management.field_definition_post_delete',
        )
