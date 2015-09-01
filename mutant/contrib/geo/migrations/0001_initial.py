# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mutant', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GeometryFieldDefinition',
            fields=[
                ('fielddefinition_ptr', models.OneToOneField(
                    to='mutant.FieldDefinition', on_delete=models.CASCADE, parent_link=True, auto_created=True,
                    primary_key=True, serialize=False
                )),
                ('srid', models.IntegerField(default=4326, help_text='Spatial Reference System Identity', verbose_name='SRID')),
                ('spatial_index', models.BooleanField(default=True, help_text='Creates a spatial index for the given geometry field.', verbose_name='spatial index')),
                ('dim', models.PositiveSmallIntegerField(default=2, help_text='Coordinate dimension.', verbose_name='coordinate dimension', choices=[(2, 'Two-dimensional'), (3, 'Three-dimensional')])),
                ('geography', models.BooleanField(default=False, help_text='Creates a database column of type geography, rather than geometry.', verbose_name='geography')),
            ],
            options={
                'db_table': 'mutant_geometryfielddefinition',
            },
            bases=('mutant.fielddefinition',),
        ),
        migrations.CreateModel(
            name='GeometryCollectionFieldDefinition',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('geo.geometryfielddefinition',),
        ),
        migrations.CreateModel(
            name='LineStringFieldDefinition',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('geo.geometryfielddefinition',),
        ),
        migrations.CreateModel(
            name='MultiLineStringFieldDefinition',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('geo.geometryfielddefinition',),
        ),
        migrations.CreateModel(
            name='MultiPointFieldDefinition',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('geo.geometryfielddefinition',),
        ),
        migrations.CreateModel(
            name='MultiPolygonFieldDefinition',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('geo.geometryfielddefinition',),
        ),
        migrations.CreateModel(
            name='PointFieldDefinition',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('geo.geometryfielddefinition',),
        ),
        migrations.CreateModel(
            name='PolygonFieldDefinition',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('geo.geometryfielddefinition',),
        ),
    ]
