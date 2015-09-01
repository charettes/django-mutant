# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mutant', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DateFieldDefinition',
            fields=[
                ('fielddefinition_ptr', models.OneToOneField(
                    to='mutant.FieldDefinition', on_delete=models.CASCADE, parent_link=True, auto_created=True,
                    primary_key=True, serialize=False
                )),
                ('auto_now', models.BooleanField(default=False, help_text='Automatically set the field to now every time the object is saved.', verbose_name='auto now')),
                ('auto_now_add', models.BooleanField(default=False, help_text='Automatically set the field to now when the object is first created.', verbose_name='auto now add')),
            ],
            options={
                'db_table': 'mutant_datefielddefinition',
            },
            bases=('mutant.fielddefinition',),
        ),
        migrations.CreateModel(
            name='DateTimeFieldDefinition',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('temporal.datefielddefinition',),
        ),
        migrations.CreateModel(
            name='TimeFieldDefinition',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('temporal.datefielddefinition',),
        ),
    ]
