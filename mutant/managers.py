from __future__ import unicode_literals

from django.db import models


class FilteredQuerysetManager(models.Manager):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        super(FilteredQuerysetManager, self).__init__()

    def get_queryset(self):
        qs = super(FilteredQuerysetManager, self).get_queryset()
        return qs.filter(*self.args, **self.kwargs)
