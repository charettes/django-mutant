
from django.contrib.gis.db import models
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _

from ....management import FIELD_DEFINITION_POST_SAVE_UID
from ....models import FieldDefinition, FieldDefinitionBase

from ..management import geometry_field_definition_post_save


class GeometryFieldDefinitionBase(FieldDefinitionBase):
    """
    Replace `post_save` connected signal by a wrapper that execute deferred sql
    required for some geometry field creation when relying on south
    """
    def __new__(cls, name, parents, attrs):
        definition = super(GeometryFieldDefinitionBase, cls).__new__(cls, name, parents, attrs)
        model = definition._meta.object_name.lower()
        post_save.disconnect(sender=definition,
                             dispatch_uid=FIELD_DEFINITION_POST_SAVE_UID % model)
        post_save.connect(geometry_field_definition_post_save, definition)
        return definition

DIM_CHOICES = (
    (2, _(u'Two-dimensional')),
    (3, _(u'Three-dimensional')),
)

srid_help_text = _(u'Spatial Reference System Identity')

spatial_index_help_text = _(u'Creates a spatial index for the given '
                            u'geometry field.')

dim_help_text = _(u'Coordinate dimension.')

geography_help_text = _(u'Creates a database column of type geography, '
                        u'rather than geometry.')

class GeometryFieldDefinition(FieldDefinition):
    
    __metaclass__ = GeometryFieldDefinitionBase
    
    srid = models.IntegerField(_(u'SRID'), default=4326,
                               help_text=srid_help_text)
    spatial_index = models.BooleanField(_(u'spatial index'), default=True,
                                        help_text=spatial_index_help_text)
    dim = models.PositiveSmallIntegerField(_(u'coordinate dimension'),
                                           choices=DIM_CHOICES, default=2,
                                           help_text=dim_help_text)
    geography = models.BooleanField(_(u'geography'), default=False,
                                    help_text=geography_help_text)
    
    class Meta:
        app_label = 'mutant'
        defined_field_class = models.GeometryField
        defined_field_options = ('srid', 'spatial_index', 'dim', 'geography')
        defined_field_category = _(u'geometry')

class PointFieldDefinition(GeometryFieldDefinition):
    
    class Meta:
        app_label = 'mutant'
        proxy = True
        verbose_name = _(u'point field')
        verbose_name_plural = _(u'point fields')
        defined_field_class = models.PointField
        
class LineStringFieldDefinition(GeometryFieldDefinition):
    
    class Meta:
        app_label = 'mutant'
        proxy = True
        verbose_name = _(u'line string field')
        verbose_name_plural = _(u'line string fields')
        defined_field_class = models.LineStringField
        
class PolygonFieldDefinition(GeometryFieldDefinition):
    
    class Meta:
        app_label = 'mutant'
        proxy = True
        verbose_name = _(u'polygon field')
        verbose_name_plural = _(u'polygon fields')
        defined_field_class = models.PolygonField

class MultiPointFieldDefinition(GeometryFieldDefinition):
    
    class Meta:
        app_label = 'mutant'
        proxy = True
        verbose_name = _(u'multi point field')
        verbose_name_plural = _(u'multi point fields')
        defined_field_class = models.MultiPointField
        
class MultiLineStringFieldDefinition(GeometryFieldDefinition):
    
    class Meta:
        app_label = 'mutant'
        proxy = True
        verbose_name = _(u'multi line string field')
        verbose_name_plural = _(u'multi line string fields')
        defined_field_class = models.MultiLineStringField

class MultiPolygonFieldDefinition(GeometryFieldDefinition):
    
    class Meta:
        app_label = 'mutant'
        proxy = True
        verbose_name = _(u'multi polygon field')
        verbose_name_plural = _(u'multi polygon fields')
        defined_field_class = models.MultiPolygonField

class GeometryCollectionFieldDefinition(GeometryFieldDefinition):
    
    class Meta:
        app_label = 'mutant'
        proxy = True
        verbose_name = _(u'geometry collection field')
        verbose_name_plural = _(u'geometry collection fields')
        defined_field_class = models.GeometryCollectionField
