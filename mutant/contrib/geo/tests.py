
from django.contrib.gis.geos import (GeometryCollection, LineString, Point,
    Polygon, MultiLineString, MultiPoint, MultiPolygon)
from django.db.utils import IntegrityError

from .models import (GeoModel, GeometryCollectionFieldDefinition,
    LineStringFieldDefinition, PointFieldDefinition, PolygonFieldDefinition,
    MultiLineStringFieldDefinition, MultiPointFieldDefinition,
    MultiPolygonFieldDefinition)
from ...models import BaseDefinition
from ...tests.models import BaseModelDefinitionTestCase


class FieldDefinitionTestMixin(object):
    
    field_defintion_init_kwargs = {}
    field_values = ()
    
    def setUp(self):
        super(GeometryFieldDefinitionBaseTest, self).setUp()
        self.field = self.field_definition_cls.objects.create(model_def=self.model_def,
                                                              name='field',
                                                              **self.field_defintion_init_kwargs)
        
    def test_field_default(self):
        default, field = self.field_values[0], self.field
        
        field.default = default
        field.full_clean()
        field.save()
        
        Model = self.model_def.model_class()
        instance = Model.objects.create()
        self.assertEqual(instance.field, default)
        
    def test_model_save(self):
        first_value, second_value = self.field_values
        
        Model = self.model_def.model_class()
        instance = Model.objects.create(field=first_value)
        self.assertEqual(instance.field, first_value)
        
        instance.field = second_value
        instance.save()
        instance = Model.objects.get()
        self.assertEqual(instance.field, second_value)
        
    def test_field_renaming(self):
        value = self.field_values[0]
        Model = self.model_def.model_class()
        
        Model.objects.create(field=value)
        
        self.field.name = 'renamed_field'
        self.field.save()
        
        instance = Model.objects.get()
        self.assertEqual(instance.renamed_field, value)
        
        msg = "'field' is an invalid keyword argument for this function"
        self.assertRaisesMessage(TypeError, msg, Model, field=value)
        
        Model.objects.create(renamed_field=value)
        
    def test_field_deletion(self):
        value = self.field_values[0]
        Model = self.model_def.model_class()
        
        Model.objects.create(field=value)

        self.field.delete()
        
        msg = "'field' is an invalid keyword argument for this function"
        self.assertRaisesMessage(TypeError, msg, Model, field=value)
        
    def test_field_unique(self):
        value = self.field_values[0]
        Model = self.model_def.model_class()
        
        self.field.unique = True
        self.field.save()
        
        Model.objects.create(field=value)
        with self.assertRaises(IntegrityError):
            Model.objects.create(field=value)

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
    