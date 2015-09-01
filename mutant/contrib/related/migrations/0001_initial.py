# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import picklefield.fields
from django.db import migrations, models

import mutant.db.fields.python


class Migration(migrations.Migration):

    dependencies = [
        ('mutant', '0001_initial'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ForeignKeyDefinition',
            fields=[
                ('fielddefinition_ptr', models.OneToOneField(
                    to='mutant.FieldDefinition', on_delete=models.CASCADE, parent_link=True, auto_created=True,
                    primary_key=True, serialize=False
                )),
                ('related_name', mutant.db.fields.python.PythonIdentifierField(help_text='The name to use for the relation from the related object back to this one.', max_length=255, null=True, verbose_name='related name', blank=True)),
                ('to_field', mutant.db.fields.python.PythonIdentifierField(help_text='The field on the related object that the relation is to.', max_length=255, null=True, verbose_name='to field', blank=True)),
                ('one_to_one', models.BooleanField(default=False, editable=False)),
                ('on_delete', models.CharField(default='CASCADE', choices=[('CASCADE', 'CASCADE'), ('PROTECT', 'PROTECT'), ('SET_NULL', 'SET_NULL'), ('SET_DEFAULT', 'SET_DEFAULT'), ('SET_VALUE', 'SET(VALUE)'), ('DO_NOTHING', 'DO_NOTHING')], max_length=11, blank=True, help_text='Behavior when an object referenced by this field is deleted', null=True, verbose_name='on delete')),
                ('on_delete_set_value', picklefield.fields.PickledObjectField(verbose_name='on delete set value', null=True, editable=False)),
                ('to', models.ForeignKey(
                    to='contenttypes.ContentType', on_delete=models.CASCADE, related_name='+', verbose_name='to'
                )),
            ],
            options={
                'db_table': 'mutant_foreignkeydefinition',
            },
            bases=('mutant.fielddefinition',),
        ),
        migrations.CreateModel(
            name='ManyToManyFieldDefinition',
            fields=[
                ('fielddefinition_ptr', models.OneToOneField(
                    to='mutant.FieldDefinition', on_delete=models.CASCADE, parent_link=True, auto_created=True,
                    primary_key=True, serialize=False
                )),
                ('related_name', mutant.db.fields.python.PythonIdentifierField(help_text='The name to use for the relation from the related object back to this one.', max_length=255, null=True, verbose_name='related name', blank=True)),
                ('symmetrical', models.NullBooleanField(verbose_name='symmetrical')),
                ('db_table', models.SlugField(help_text='The name of the table to create for storing the many-to-many data', max_length=30, null=True, blank=True)),
                ('through', models.ForeignKey(
                    to='contenttypes.ContentType', on_delete=models.CASCADE, related_name='+', blank=True, help_text='Intermediary model', null=True)),
                ('to', models.ForeignKey(
                    to='contenttypes.ContentType', on_delete=models.CASCADE, related_name='+', verbose_name='to'
                )),
            ],
            options={
                'db_table': 'mutant_manytomanyfielddefinition',
            },
            bases=('mutant.fielddefinition',),
        ),
        migrations.CreateModel(
            name='OneToOneFieldDefinition',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('related.foreignkeydefinition',),
        ),
    ]
