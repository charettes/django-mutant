
from django.contrib.gis.geos import (GeometryCollection, LineString, Point,
    Polygon, MultiLineString, MultiPoint, MultiPolygon)

from ...models import BaseDefinition
from ...test.testcases import FieldDefinitionTestMixin
from ...tests.models import BaseModelDefinitionTestCase

from .models import (GeoModel, GeometryCollectionFieldDefinition,
    LineStringFieldDefinition, PointFieldDefinition, PolygonFieldDefinition,
    MultiLineStringFieldDefinition, MultiPointFieldDefinition,
    MultiPolygonFieldDefinition)


class GeometryFieldDefinitionBaseTest(BaseModelDefinitionTestCase):
    
    def setUp(self):
        super(GeometryFieldDefinitionBaseTest, self).setUp()
        BaseDefinition.objects.create(model_def=self.model_def, base=GeoModel)

class PointFieldDefinitionTest(FieldDefinitionTestMixin,
                               GeometryFieldDefinitionBaseTest):
    field_definition_cls = PointFieldDefinition
    field_values = (Point(5, 23), Point(13, 37))
    
class LineStringFieldDefinitionTest(FieldDefinitionTestMixin,
                                    GeometryFieldDefinitionBaseTest):
    field_definition_cls = LineStringFieldDefinition
    field_values = (
        LineString((0, 0), (0, 50), (50, 50), (50, 0), (0, 0)),
        LineString((1, 2), (3, 4), (5, 6), (7, 8), (9, 10))
    )

class PolygonFieldDefinitionTest(FieldDefinitionTestMixin,
                                 GeometryFieldDefinitionBaseTest):
    field_definition_cls = PolygonFieldDefinition
    field_values = (
        Polygon( ((0.0, 0.0), (0.0, 50.0), (50.0, 50.0), (50.0, 0.0), (0.0, 0.0)) ),
        Polygon( ((0.0, 0.0), (18, 50.0), (47.0, 55.0), (50.0, 0.0), (0.0, 0.0)) ),
    )

class MultiLineStringFieldDefinitionTest(FieldDefinitionTestMixin,
                                         GeometryFieldDefinitionBaseTest):
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

class MultiPointFieldDefinitionTest(FieldDefinitionTestMixin,
                                    GeometryFieldDefinitionBaseTest):
    field_definition_cls = MultiPointFieldDefinition
    field_values = (
        MultiPoint(Point(0, 0), Point(1, 1)),
        MultiPoint(Point(5, 23), Point(13, 37), Point(13, 58)),
    )
    
class MultiPolygonFieldDefinitionTest(FieldDefinitionTestMixin,
                                      GeometryFieldDefinitionBaseTest):
    field_definition_cls = MultiPolygonFieldDefinition
    field_values = (
        MultiPolygon(
            Polygon( ((0.0, 0.0), (0.0, 50.0), (50.0, 50.0), (50.0, 0.0), (0.0, 0.0)) ),
            Polygon( ((0.0, 0.0), (18, 50.0), (47.0, 55.0), (50.0, 0.0), (0.0, 0.0)) ),
        ),
        MultiPolygon(
            Polygon( ((0.0, 0.0), (0.0, 50.0), (50.0, 50.0), (50.0, 0.0), (0.0, 0.0)) ),
            Polygon( ((0.0, 0.0), (18, 50.0), (47.0, 55.0), (50.0, 0.0), (0.0, 0.0)) ),
            Polygon( ((0.0, 0.0), (0.0, 50.0), (50.0, 51.0), (50.0, 45), (0.0, 0.0)) ),
        ),
    )

class GeometryCollectionFieldDefinitionTest(FieldDefinitionTestMixin,
                                            GeometryFieldDefinitionBaseTest):
    field_definition_cls = GeometryCollectionFieldDefinition
    field_values = (
        GeometryCollection(
            Point(0, 0),
            Polygon( ((0.0, 0.0), (18, 50.0), (47.0, 55.0), (50.0, 0.0), (0.0, 0.0)) ),
        ),
        GeometryCollection(
            LineString((1, 2), (3, 4), (5, 6), (7, 8), (9, 10)),
            Polygon( ((0.0, 0.0), (18, 50.0), (47.0, 55.0), (50.0, 0.0), (0.0, 0.0)) ),
            Point(5, 23),
            Point(13, 37),
        ),
    )
    
