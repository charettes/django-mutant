from __future__ import unicode_literals

from django.db import models


class ModelDefinitionManager(models.Manager):
    use_for_related_fields = True

    def get_by_natural_key(self, app_label, model):
        return self.get(app_label=app_label, model=model)
