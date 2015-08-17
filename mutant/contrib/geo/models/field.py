from __future__ import unicode_literals

from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _

from mutant.models import FieldDefinition, FieldDefinitionManager

srid_help_text = _('Spatial Reference System Identity')
spatial_index_help_text = _('Creates a spatial index for the given '
                            'geometry field.')
dim_help_text = _('Coordinate dimension.')
geography_help_text = _('Creates a database column of type geography, '
                        'rather than geometry.')


class GeometryFieldDefinition(FieldDefinition):
    DIM_2D = 2
    DIM_3D = 3
    DIM_CHOICES = (
        (DIM_2D, _('Two-dimensional')),
        (DIM_3D, _('Three-dimensional')),
    )

    srid = models.IntegerField(_('SRID'), default=4326,
                               help_text=srid_help_text)
    spatial_index = models.BooleanField(_('spatial index'), default=True,
                                        help_text=spatial_index_help_text)
    dim = models.PositiveSmallIntegerField(_('coordinate dimension'),
                                           choices=DIM_CHOICES, default=2,
                                           help_text=dim_help_text)
    geography = models.BooleanField(_('geography'), default=False,
                                    help_text=geography_help_text)

    objects = FieldDefinitionManager()

    class Meta:
        app_label = 'geo'
        defined_field_options = ('srid', 'spatial_index', 'dim', 'geography')
        defined_field_category = _('Geometry')
        defined_field_class = models.GeometryField


class PointFieldDefinition(GeometryFieldDefinition):
    class Meta:
        app_label = 'geo'
        proxy = True
        defined_field_class = models.PointField


class LineStringFieldDefinition(GeometryFieldDefinition):
    class Meta:
        app_label = 'geo'
        proxy = True
        defined_field_class = models.LineStringField


class PolygonFieldDefinition(GeometryFieldDefinition):
    class Meta:
        app_label = 'geo'
        proxy = True
        defined_field_class = models.PolygonField


class MultiPointFieldDefinition(GeometryFieldDefinition):
    class Meta:
        app_label = 'geo'
        proxy = True
        defined_field_class = models.MultiPointField


class MultiLineStringFieldDefinition(GeometryFieldDefinition):
    class Meta:
        app_label = 'geo'
        proxy = True
        defined_field_class = models.MultiLineStringField


class MultiPolygonFieldDefinition(GeometryFieldDefinition):
    class Meta:
        app_label = 'geo'
        proxy = True
        defined_field_class = models.MultiPolygonField


class GeometryCollectionFieldDefinition(GeometryFieldDefinition):
    class Meta:
        app_label = 'geo'
        proxy = True
        defined_field_class = models.GeometryCollectionField
