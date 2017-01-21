from __future__ import unicode_literals

import django
from django.db import models


class ModelDefinitionQuerySet(models.QuerySet):
    def _extract_model_params(self, defaults, **kwargs):
        # Work around get/update_or_create validations of parameters to allow
        # bases and fields to be passed to ModelDefinition's initializer.
        bases = defaults.pop('bases', None)
        fields = defaults.pop('fields', None)
        lookup, params = super(ModelDefinitionQuerySet, self)._extract_model_params(defaults, **kwargs)
        if bases is not None:
            params['bases'] = bases
        if fields is not None:
            params['fields'] = fields
        return lookup, params

    def get_by_natural_key(self, app_label, model):
        return self.get(app_label=app_label, model=model)


class ModelDefinitionManager(models.Manager.from_queryset(ModelDefinitionQuerySet)):
    if django.VERSION < (1, 10):
        use_for_related_fields = True
