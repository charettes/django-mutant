from __future__ import unicode_literals

import warnings

import django
from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


# TODO: Remove when support for Django 1.5 is dropped.
if django.VERSION < (1, 7):
    class ProxyAwareGenericForeignKey(GenericForeignKey):
        """
        Basically a GenericForeignKey that saves the actual ContentType of the
        object even if it's a proxy Model.
        """
        if django.VERSION >= (1, 6):
            def __init__(self, *args, **kwargs):
                warnings.warn(
                    '`ProxyAwareGenericForeignKey` is deprecated on Django >= '
                    '1.6. Use `GenericForeignKey` with the '
                    '`for_concrete_model=False` kwarg instead.',
                    DeprecationWarning, stacklevel=2
                )
                super(ProxyAwareGenericForeignKey, self).__init__(*args, **kwargs)

        def get_content_type(self, obj=None, **kwargs):
            if obj:
                return ContentType.objects.db_manager(obj._state.db).get_for_model(
                    obj.__class__, for_concrete_model=False
                )
            else:
                return super(ProxyAwareGenericForeignKey, self).get_content_type(obj, **kwargs)
