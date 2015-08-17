# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mutant', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BooleanFieldDefinition',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('mutant.fielddefinition',),
        ),
        migrations.CreateModel(
            name='NullBooleanFieldDefinition',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('mutant.fielddefinition',),
        ),
    ]
