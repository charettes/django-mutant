from __future__ import unicode_literals

from django.apps import AppConfig

from ...signals import mutable_class_prepared


class RelatedConfig(AppConfig):
    name = 'mutant.contrib.related'

    def ready(self):
        from . import management
        mutable_class_prepared.connect(management.mutable_model_prepared)
