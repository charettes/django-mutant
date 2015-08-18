from __future__ import unicode_literals

from django.apps import AppConfig
from django.db import models

from ...signals import mutable_class_prepared


class RelatedConfig(AppConfig):
    name = 'mutant.contrib.related'

    def ready(self):
        from . import management

        mutable_class_prepared.connect(management.mutable_model_prepared)

        ManyToManyFieldDefinition = self.get_model('ManyToManyFieldDefinition')
        models.signals.pre_delete.connect(
            management.many_to_many_field_definition_pre_delete,
            sender=ManyToManyFieldDefinition,
            dispatch_uid='mutant.contrib.related.management.many_to_many_field_definition_pre_delete',
        )
        models.signals.post_delete.connect(
            management.many_to_many_field_definition_post_delete,
            sender=ManyToManyFieldDefinition,
            dispatch_uid='mutant.contrib.related.management.many_to_many_field_definition_post_delete',
        )
