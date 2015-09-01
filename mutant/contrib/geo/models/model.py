from __future__ import unicode_literals

import django
from django.contrib.gis.db import models

GeoManager = models.Manager if django.VERSION >= (1, 9) else models.GeoManager


class GeoModel(models.Model):
    """
    A model to be used as a BaseDefinition on ModelDefinition instance with
    GeometryFieldDefinition instances.
    """
    objects = GeoManager()

    class Meta:
        abstract = True
