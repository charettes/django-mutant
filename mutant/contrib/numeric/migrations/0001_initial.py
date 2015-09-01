# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mutant', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DecimalFieldDefinition',
            fields=[
                ('fielddefinition_ptr', models.OneToOneField(
                    to='mutant.FieldDefinition', on_delete=models.CASCADE, parent_link=True, auto_created=True,
                    primary_key=True, serialize=False
                )),
                ('max_digits', models.PositiveSmallIntegerField(help_text='The maximum number of digits allowed in the number. Note that this number must be greater than or equal to ``decimal_places``, if it exists.', verbose_name='max digits')),
                ('decimal_places', models.PositiveSmallIntegerField(help_text='The number of decimal places to store with the number.', verbose_name='decimal_places')),
            ],
            options={
                'db_table': 'mutant_decimalfielddefinition',
            },
            bases=('mutant.fielddefinition',),
        ),
        migrations.CreateModel(
            name='BigIntegerFieldDefinition',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('mutant.fielddefinition',),
        ),
        migrations.CreateModel(
            name='FloatFieldDefinition',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('mutant.fielddefinition',),
        ),
        migrations.CreateModel(
            name='IntegerFieldDefinition',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('mutant.fielddefinition',),
        ),
        migrations.CreateModel(
            name='PositiveIntegerFieldDefinition',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('mutant.fielddefinition',),
        ),
        migrations.CreateModel(
            name='PositiveSmallIntegerFieldDefinition',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('mutant.fielddefinition',),
        ),
        migrations.CreateModel(
            name='SmallIntegerFieldDefinition',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('mutant.fielddefinition',),
        ),
    ]
