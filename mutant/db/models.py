from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db import models
from django.db.migrations.state import ModelState
from django.utils.six import string_types
from django.utils.translation import ugettext_lazy as _

from .. import logger
from ..compat import get_remote_field_model, StateApps
from ..state import handler as state_handler


class MutableModel(models.Model):
    """Abstract class used to identify models that we're created by a
    definition."""

    class Meta:
        abstract = True

    @classmethod
    def definition(cls):
        definition_cls, definition_pk = cls._definition
        return definition_cls.objects.get(pk=definition_pk)

    @classmethod
    def checksum(cls):
        return cls._checksum

    @classmethod
    def is_obsolete(cls):
        return (
            cls._is_obsolete or
            cls._checksum != state_handler.get_checksum(cls._definition[1])
        )

    @classmethod
    def get_model_state(cls):
        return ModelState.from_model(cls)

    @classmethod
    def render_state(cls):
        state = cls.get_model_state()
        model_states = {(state.app_label, state.name): state}
        for _name, field in state.fields:
            related_model = get_remote_field_model(field)
            if related_model:
                related_model_state = ModelState.from_model(
                    cls._meta.apps.get_model(related_model), exclude_rels=True
                )
                model_states[related_model_state.app_label, related_model_state.name] = related_model_state
                for base in related_model_state.bases:
                    if isinstance(base, string_types):
                        base_model_state = ModelState.from_model(
                            cls._meta.apps.get_model(base), exclude_rels=True
                        )
                        model_states[base_model_state.app_label, base_model_state.name] = base_model_state
        apps = StateApps([], {})
        apps.render_multiple(model_states.values())
        return apps.all_models[state.app_label][state.name.lower()]

    @classmethod
    def mark_as_obsolete(cls, origin=None):
        cls._is_obsolete = True
        logger.debug(
            "Marking model %s and it dependencies (%s) as obsolete.",
            cls, cls._dependencies
        )
        if origin is None:
            origin = cls._definition
        for definition_cls, definition_pk in cls._dependencies:
            if (definition_cls, definition_pk) == origin:
                continue
            try:
                definition = definition_cls.objects.get(pk=definition_pk)
            except definition_cls.DoesNotExist:
                pass
            else:
                definition.model_class().mark_as_obsolete(origin)

    def clean(self):
        if self.is_obsolete():
            raise ValidationError('Obsolete definition')
        return super(MutableModel, self).clean()

    def save(self, *args, **kwargs):
        if self.is_obsolete():
            msg = _('Cannot save an obsolete model')
            raise ValidationError(msg)
        return super(MutableModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.is_obsolete():
            msg = _('Cannot delete an obsolete model')
            raise ValidationError(msg)
        return super(MutableModel, self).delete(*args, **kwargs)
