# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mutant', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CharFieldDefinition',
            fields=[
                ('fielddefinition_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='mutant.FieldDefinition')),
                ('max_length', models.PositiveSmallIntegerField(null=True, verbose_name='max length', blank=True)),
            ],
            options={
                'db_table': 'mutant_charfielddefinition',
            },
            bases=('mutant.fielddefinition',),
        ),
        migrations.CreateModel(
            name='TextFieldDefinition',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('text.charfielddefinition',),
        ),
    ]
