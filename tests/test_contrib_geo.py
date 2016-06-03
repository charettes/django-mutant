from __future__ import unicode_literals

from django.contrib.gis.geos import (
    GeometryCollection, LineString, MultiLineString, MultiPoint, MultiPolygon,
    Point, Polygon,
)
from django.db import connection
from django.test.utils import skipUnless
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _

from mutant.models import BaseDefinition
from mutant.test.testcases import FieldDefinitionTestMixin

from .utils import BaseModelDefinitionTestCase


class GeometryFieldDefinitionTestMixin(FieldDefinitionTestMixin):
    field_definition_category = _('Geometry')

    @classmethod
    def setUpTestData(cls):
        cls.field_definition_cls = import_string("mutant.contrib.geo.models.%s" % cls.field_definition_cls_name)
        super(GeometryFieldDefinitionTestMixin, cls).setUpTestData()
        from mutant.contrib.geo.models import GeoModel
        BaseDefinition.objects.create(model_def_id=cls.model_def_pk, base=GeoModel)


@skipUnless(connection.settings_dict['ENGINE'] == 'django.contrib.gis.db.backends.postgis', 'Requires GIS backend.')
class GeometryFieldDefinitionTest(GeometryFieldDefinitionTestMixin,
                                  BaseModelDefinitionTestCase):
    field_definition_cls_name = 'GeometryFieldDefinition'
    field_values = (
        LineString((1, 2), (3, 4), (5, 6), (7, 8), (9, 10)),
        Polygon(
            ((0.0, 0.0), (18, 50.0), (47.0, 55.0), (50.0, 0.0), (0.0, 0.0))
        )
    )


@skipUnless(connection.settings_dict['ENGINE'] == 'django.contrib.gis.db.backends.postgis', 'Requires GIS backend.')
class PointFieldDefinitionTest(GeometryFieldDefinitionTestMixin,
                               BaseModelDefinitionTestCase):
    field_definition_cls_name = 'PointFieldDefinition'
    field_values = (Point(5, 23), Point(13, 37))


@skipUnless(connection.settings_dict['ENGINE'] == 'django.contrib.gis.db.backends.postgis', 'Requires GIS backend.')
class LineStringFieldDefinitionTest(GeometryFieldDefinitionTestMixin,
                                    BaseModelDefinitionTestCase):
    field_definition_cls_name = 'LineStringFieldDefinition'
    field_values = (
        LineString((0, 0), (0, 50), (50, 50), (50, 0), (0, 0)),
        LineString((1, 2), (3, 4), (5, 6), (7, 8), (9, 10))
    )


@skipUnless(connection.settings_dict['ENGINE'] == 'django.contrib.gis.db.backends.postgis', 'Requires GIS backend.')
class PolygonFieldDefinitionTest(GeometryFieldDefinitionTestMixin,
                                 BaseModelDefinitionTestCase):
    field_definition_cls_name = 'PolygonFieldDefinition'
    field_values = (
        Polygon(
            ((0.0, 0.0), (0.0, 50.0), (50.0, 50.0), (50.0, 0.0), (0.0, 0.0))
        ),
        Polygon(
            ((0.0, 0.0), (18, 50.0), (47.0, 55.0), (50.0, 0.0), (0.0, 0.0))
        ),
    )


@skipUnless(connection.settings_dict['ENGINE'] == 'django.contrib.gis.db.backends.postgis', 'Requires GIS backend.')
class MultiLineStringFieldDefinitionTest(GeometryFieldDefinitionTestMixin,
                                         BaseModelDefinitionTestCase):
    field_definition_cls_name = 'MultiLineStringFieldDefinition'
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


@skipUnless(connection.settings_dict['ENGINE'] == 'django.contrib.gis.db.backends.postgis', 'Requires GIS backend.')
class MultiPointFieldDefinitionTest(GeometryFieldDefinitionTestMixin,
                                    BaseModelDefinitionTestCase):
    field_definition_cls_name = 'MultiPointFieldDefinition'
    field_values = (
        MultiPoint(Point(0, 0), Point(1, 1)),
        MultiPoint(Point(5, 23), Point(13, 37), Point(13, 58)),
    )


@skipUnless(connection.settings_dict['ENGINE'] == 'django.contrib.gis.db.backends.postgis', 'Requires GIS backend.')
class MultiPolygonFieldDefinitionTest(GeometryFieldDefinitionTestMixin,
                                      BaseModelDefinitionTestCase):
    field_definition_cls_name = 'MultiPolygonFieldDefinition'
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


@skipUnless(connection.settings_dict['ENGINE'] == 'django.contrib.gis.db.backends.postgis', 'Requires GIS backend.')
class GeometryCollectionFieldDefinitionTest(GeometryFieldDefinitionTestMixin,
                                            BaseModelDefinitionTestCase):
    field_definition_cls_name = 'GeometryCollectionFieldDefinition'
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
