from __future__ import unicode_literals

import sys
# TODO: Remove when support for Python 2.6 is dropped
if sys.version_info >= (2, 7):
    from unittest import expectedFailure
else:
    from django.utils.unittest import expectedFailure

from django.contrib.gis.geos import (GeometryCollection, LineString, Point,
    Polygon, MultiLineString, MultiPoint, MultiPolygon)
from django.utils.translation import ugettext_lazy as _

from mutant.models import BaseDefinition
from mutant.test.testcases import FieldDefinitionTestMixin
from mutant.tests.utils import BaseModelDefinitionTestCase

from .models import (GeoModel, GeometryFieldDefinition,
    GeometryCollectionFieldDefinition, LineStringFieldDefinition,
    PointFieldDefinition, PolygonFieldDefinition,
    MultiLineStringFieldDefinition, MultiPointFieldDefinition,
    MultiPolygonFieldDefinition)


class GeometryFieldDefinitionTestMixin(FieldDefinitionTestMixin):
    field_definition_category = _('Geometry')

    def setUp(self):
        super(GeometryFieldDefinitionTestMixin, self).setUp()
        BaseDefinition.objects.create(model_def=self.model_def, base=GeoModel)

    @expectedFailure
    def test_create_with_default(self):
        """'Geometry field defaults are not correctly handled by South.'"""
        super(GeometryFieldDefinitionTestMixin, self).test_create_with_default()


class GeometryFieldDefinitionTest(GeometryFieldDefinitionTestMixin,
                                  BaseModelDefinitionTestCase):
    field_definition_cls = GeometryFieldDefinition
    field_values = (
        LineString((1, 2), (3, 4), (5, 6), (7, 8), (9, 10)),
        Polygon(
            ((0.0, 0.0), (18, 50.0), (47.0, 55.0), (50.0, 0.0), (0.0, 0.0))
        )
    )


class PointFieldDefinitionTest(GeometryFieldDefinitionTestMixin,
                               BaseModelDefinitionTestCase):
    field_definition_cls = PointFieldDefinition
    field_values = (Point(5, 23), Point(13, 37))


class LineStringFieldDefinitionTest(GeometryFieldDefinitionTestMixin,
                                    BaseModelDefinitionTestCase):
    field_definition_cls = LineStringFieldDefinition
    field_values = (
        LineString((0, 0), (0, 50), (50, 50), (50, 0), (0, 0)),
        LineString((1, 2), (3, 4), (5, 6), (7, 8), (9, 10))
    )


class PolygonFieldDefinitionTest(GeometryFieldDefinitionTestMixin,
                                 BaseModelDefinitionTestCase):
    field_definition_cls = PolygonFieldDefinition
    field_values = (
        Polygon(
            ((0.0, 0.0), (0.0, 50.0), (50.0, 50.0), (50.0, 0.0), (0.0, 0.0))
        ),
        Polygon(
            ((0.0, 0.0), (18, 50.0), (47.0, 55.0), (50.0, 0.0), (0.0, 0.0))
        ),
    )


class MultiLineStringFieldDefinitionTest(GeometryFieldDefinitionTestMixin,
                                         BaseModelDefinitionTestCase):
    field_definition_cls = MultiLineStringFieldDefinition
    field_values = (
        MultiLineString(
            LineString((0, 0), (0, 50), (50, 50), (50, 0), (0, 0)),
            LineString((1, 2), (3, 4), (5, 6), (7, 8), (9, 10)),
        ),
        MultiLineString(
            LineString((13, 7), (18, 50), (50, 50), (50, 27), (110, 0)),
            LineString((1, 2), (3, 4), (5, 6), (7, 8), (9, 10)),
            LineString((0, 0), (0, 50), (50, 50), (50, 0), (0, 0)),
        ),
    )


class MultiPointFieldDefinitionTest(GeometryFieldDefinitionTestMixin,
                                    BaseModelDefinitionTestCase):
    field_definition_cls = MultiPointFieldDefinition
    field_values = (
        MultiPoint(Point(0, 0), Point(1, 1)),
        MultiPoint(Point(5, 23), Point(13, 37), Point(13, 58)),
    )


class MultiPolygonFieldDefinitionTest(GeometryFieldDefinitionTestMixin,
                                      BaseModelDefinitionTestCase):
    field_definition_cls = MultiPolygonFieldDefinition
    field_values = (
        MultiPolygon(
            Polygon(
                ((0.0, 0.0), (0.0, 50.0), (50.0, 50.0), (50.0, 0.0), (0.0, 0.0))
            ),
            Polygon(
                ((0.0, 0.0), (18, 50.0), (47.0, 55.0), (50.0, 0.0), (0.0, 0.0))
            ),
        ),
        MultiPolygon(
            Polygon(
                ((0.0, 0.0), (0.0, 50.0), (50.0, 50.0), (50.0, 0.0), (0.0, 0.0))
            ),
            Polygon(
                ((0.0, 0.0), (18, 50.0), (47.0, 55.0), (50.0, 0.0), (0.0, 0.0))
            ),
            Polygon(
                ((0.0, 0.0), (0.0, 50.0), (50.0, 51.0), (50.0, 45), (0.0, 0.0))
            ),
        ),
    )


class GeometryCollectionFieldDefinitionTest(GeometryFieldDefinitionTestMixin,
                                            BaseModelDefinitionTestCase):
    field_definition_cls = GeometryCollectionFieldDefinition
    field_values = (
        GeometryCollection(
            Point(0, 0),
            Polygon(
                ((0.0, 0.0), (18, 50.0), (47.0, 55.0), (50.0, 0.0), (0.0, 0.0))
            ),
        ),
        GeometryCollection(
            LineString((1, 2), (3, 4), (5, 6), (7, 8), (9, 10)),
            Polygon(
                ((0.0, 0.0), (18, 50.0), (47.0, 55.0), (50.0, 0.0), (0.0, 0.0))
            ),
            Point(5, 23),
            Point(13, 37),
        ),
    )
