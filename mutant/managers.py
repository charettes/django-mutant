from __future__ import unicode_literals

import warnings

import django
from django.db import models


class FilteredQuerysetManager(models.Manager):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        super(FilteredQuerysetManager, self).__init__()

    def get_queryset(self):
        qs = super(FilteredQuerysetManager, self).get_queryset()
        return qs.filter(*self.args, **self.kwargs)

    if django.VERSION < (1, 8):
        def get_query_set(self):
            warnings.warn(
                "`FilteredQuerysetManager.get_query_set` is deprecated, "
                "use `get_queryset` instead",
                DeprecationWarning if django.VERSION >= (1, 7)
                else PendingDeprecationWarning,
                stacklevel=2
            )
            return FilteredQuerysetManager.get_queryset(self)
