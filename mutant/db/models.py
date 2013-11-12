from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .. import logger
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
