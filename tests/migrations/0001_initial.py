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
                ('fielddefinition_ptr', models.OneToOneField(
                    to='mutant.FieldDefinition', on_delete=models.CASCADE, parent_link=True, auto_created=True,
                    primary_key=True, serialize=False
                )),
            ],
            options={
            },
            bases=('mutant.fielddefinition',),
        ),
        migrations.CreateModel(
            name='FieldDefinitionModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('field_type', models.ForeignKey(
                    to='contenttypes.ContentType', on_delete=models.CASCADE,
                    related_name='+', default=polymodels.fields.ContentTypeReference('mutant', 'fielddefinition')
                )),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ModelWithModelDefinitionReference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('model_def', models.OneToOneField(
                    to='mutant.ModelDefinition', on_delete=models.CASCADE, related_name='+'
                )),
                ('nullable_model_def', models.ForeignKey(
                    to='mutant.ModelDefinition', on_delete=models.SET_NULL, related_name='+', null=True
                )),
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
