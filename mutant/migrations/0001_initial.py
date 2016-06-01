# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import picklefield.fields
import polymodels.fields
from django.db import migrations, models

import mutant.db.deletion
import mutant.db.fields.generic
import mutant.db.fields.python
import mutant.db.fields.translation
import mutant.models.field


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseDefinition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveIntegerField(editable=False)),
                ('base', picklefield.fields.PickledObjectField(verbose_name='base', editable=False)),
            ],
            options={
                'ordering': ['order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FieldDefinition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', mutant.db.fields.python.PythonIdentifierField(max_length=255, verbose_name='name')),
                ('verbose_name', mutant.db.fields.translation.LazilyTranslatedField(null=True, verbose_name='verbose name', blank=True)),
                ('help_text', mutant.db.fields.translation.LazilyTranslatedField(null=True, verbose_name='help text', blank=True)),
                ('null', models.BooleanField(default=False, verbose_name='null')),
                ('blank', models.BooleanField(default=False, verbose_name='blank')),
                ('db_column', models.SlugField(max_length=30, null=True, verbose_name='db column', blank=True)),
                ('db_index', models.BooleanField(default=False, verbose_name='db index')),
                ('editable', models.BooleanField(default=True, verbose_name='editable')),
                ('default', picklefield.fields.PickledObjectField(default=mutant.models.field.NOT_PROVIDED, verbose_name='default', null=True, editable=False)),
                ('primary_key', models.BooleanField(default=False, verbose_name='primary key')),
                ('unique', models.BooleanField(default=False, verbose_name='unique')),
                ('unique_for_date', mutant.db.fields.python.PythonIdentifierField(max_length=255, null=True, verbose_name='unique for date', blank=True)),
                ('unique_for_month', mutant.db.fields.python.PythonIdentifierField(max_length=255, null=True, verbose_name='unique for month', blank=True)),
                ('unique_for_year', mutant.db.fields.python.PythonIdentifierField(max_length=255, null=True, verbose_name='unique for year', blank=True)),
            ],
            options={
                'verbose_name': 'field',
                'verbose_name_plural': 'fields',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FieldDefinitionChoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveIntegerField(editable=False)),
                ('group', mutant.db.fields.translation.LazilyTranslatedField(null=True, verbose_name='group', blank=True)),
                ('value', picklefield.fields.PickledObjectField(verbose_name='value', editable=False)),
                ('label', mutant.db.fields.translation.LazilyTranslatedField(verbose_name='label')),
                ('field_def', models.ForeignKey(
                    to='mutant.FieldDefinition', on_delete=models.CASCADE, related_name='choices'
                )),
            ],
            options={
                'ordering': ['order'],
                'verbose_name': 'field definition choice',
                'verbose_name_plural': 'field definition choices',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ModelDefinition',
            fields=[
                ('contenttype_ptr', models.OneToOneField(
                    to='contenttypes.ContentType', on_delete=models.CASCADE, parent_link=True, auto_created=True,
                    primary_key=True, serialize=False
                )),
                ('object_name', mutant.db.fields.python.PythonIdentifierField(max_length=255, verbose_name='object name')),
                ('db_table', models.CharField(max_length=63, null=True, verbose_name='database table', blank=True)),
                ('managed', models.BooleanField(default=False, verbose_name='managed')),
                ('verbose_name', mutant.db.fields.translation.LazilyTranslatedField(null=True, verbose_name='verbose name', blank=True)),
                ('verbose_name_plural', mutant.db.fields.translation.LazilyTranslatedField(null=True, verbose_name='verbose name plural', blank=True)),
            ],
            options={
                'verbose_name': 'model definition',
                'verbose_name_plural': 'model definitions',
            },
            bases=('contenttypes.contenttype',),
        ),
        migrations.CreateModel(
            name='OrderingFieldDefinition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveIntegerField(editable=False)),
                ('lookup', models.CharField(max_length=255)),
                ('descending', models.BooleanField(default=False, verbose_name='descending')),
                ('model_def', models.ForeignKey(related_name='orderingfielddefinitions', on_delete=mutant.db.deletion.CASCADE_MARK_ORIGIN, to='mutant.ModelDefinition')),
            ],
            options={
                'ordering': ['order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UniqueTogetherDefinition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('field_defs', models.ManyToManyField(related_name='unique_together_defs', to='mutant.FieldDefinition')),
                ('model_def', models.ForeignKey(related_name='uniquetogetherdefinitions', on_delete=mutant.db.deletion.CASCADE_MARK_ORIGIN, to='mutant.ModelDefinition')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='fielddefinitionchoice',
            unique_together=set([('field_def', 'order'), ('field_def', 'group', 'value')]),
        ),
        migrations.AddField(
            model_name='fielddefinition',
            name='content_type',
            field=mutant.db.fields.generic.FieldDefinitionTypeField(),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fielddefinition',
            name='model_def',
            field=models.ForeignKey(related_name='fielddefinitions', on_delete=mutant.db.deletion.CASCADE_MARK_ORIGIN, to='mutant.ModelDefinition'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='fielddefinition',
            unique_together=set([('model_def', 'name')]),
        ),
        migrations.AddField(
            model_name='basedefinition',
            name='model_def',
            field=models.ForeignKey(related_name='basedefinitions', on_delete=mutant.db.deletion.CASCADE_MARK_ORIGIN, to='mutant.ModelDefinition'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='basedefinition',
            unique_together=set([('model_def', 'order')]),
        ),
    ]
