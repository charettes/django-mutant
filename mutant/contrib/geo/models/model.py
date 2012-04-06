
from django.contrib.gis.db import models


class GeoModel(models.Model):
    """
    A model to be used as a BaseDefinition on ModelDefinition instance with
    GeometryFieldDefinition instances 
    """
    
    objects = models.GeoManager()
    
    class Meta:
        abstract = True
