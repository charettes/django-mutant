# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import mutant.db.fields.python


class Migration(migrations.Migration):

    dependencies = [
        ('text', '0002_update_field_defs_app_label'),
    ]

    operations = [
        migrations.CreateModel(
            name='FilePathFieldDefinition',
            fields=[
                ('charfielddefinition_ptr', models.OneToOneField(
                    to='text.CharFieldDefinition', on_delete=models.CASCADE, parent_link=True,
                    auto_created=True, primary_key=True, serialize=False
                )),
                ('path', mutant.db.fields.python.DirectoryPathField(help_text='The absolute filesystem path to a directory from which this field should get its choices.', max_length=100, verbose_name='path')),
                ('match', mutant.db.fields.python.RegExpStringField(help_text='A regular expression used to filter filenames.', max_length=100, null=True, verbose_name='match', blank=True)),
                ('recursive', models.BooleanField(default=False, help_text='Specifies whether all subdirectories of path should be included', verbose_name='recursive')),
            ],
            options={
                'db_table': 'mutant_filepathfielddefinition',
            },
            bases=('text.charfielddefinition',),
        ),
    ]
