from __future__ import unicode_literals

from django.core.management.commands.loaddata import Command  # NOQA
from django.core.serializers import python as python_serializer
from django.core.serializers.base import DeserializationError

from ...models import ModelDefinition

# Monkey patch `_get_model` to attempt loading a matching model definition
# when no existing model is found.
_python_serializer_get_model = python_serializer._get_model


def _get_model(model_identifier):
    try:
        return _python_serializer_get_model(model_identifier)
    except DeserializationError as e:
        try:
            model_def = ModelDefinition.objects.get_by_natural_key(
                *model_identifier.split('.')
            )
        except ModelDefinition.DoesNotExist:
            raise e
        return model_def.model_class()

python_serializer._get_model = _get_model
