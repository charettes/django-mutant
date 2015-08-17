# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import polymodels.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mutant', '0001_initial'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConcreteModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('concrete_model_field', models.NullBooleanField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CustomFieldDefinition',
            fields=[
                ('fielddefinition_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='mutant.FieldDefinition')),
            ],
            options={
            },
            bases=('mutant.fielddefinition',),
        ),
        migrations.CreateModel(
            name='FieldDefinitionModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('field_type', models.ForeignKey(related_name='+', default=polymodels.fields.ContentTypeReference('mutant', 'fielddefinition'), to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ModelWithModelDefinitionReference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('model_def', models.OneToOneField(related_name='+', to='mutant.ModelDefinition')),
                ('nullable_model_def', models.ForeignKey(related_name='+', to='mutant.ModelDefinition', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProxyModel',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('tests.concretemodel',),
        ),
    ]
