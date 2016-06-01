from __future__ import unicode_literals

from django.db import models
from django.db.models.aggregates import Max


class OrderedModel(models.Model):
    order = models.PositiveIntegerField(editable=False)

    class Meta:
        abstract = True
        ordering = ['order']

    def get_ordering_queryset(self):
        return self.__class__._default_manager.all()

    def save(self, *args, **kwargs):
        if self.order is None:
            max_order = self.get_ordering_queryset().aggregate(
                Max('order')
            ).get('order__max')
            self.order = 0 if max_order is None else max_order + 1
        return super(OrderedModel, self).save(*args, **kwargs)
