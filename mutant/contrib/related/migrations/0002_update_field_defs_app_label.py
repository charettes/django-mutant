# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import functools

from django.db import migrations


def _update_field_def_cts_app_label(from_app_label, to_app_label, apps, schema_editor):
    cts = apps.get_model('contenttypes', 'contenttype').objects
    model_names = [
        'foreignkeydefinition',
        'manytomanyfielddefinition',
        'onetoonefielddefinition',
    ]
    cts.filter(
        app_label=from_app_label, model__in=model_names
    ).update(app_label=to_app_label)


class Migration(migrations.Migration):

    dependencies = [
        ('related', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            functools.partial(_update_field_def_cts_app_label, 'mutant', 'related'),
            functools.partial(_update_field_def_cts_app_label, 'related', 'mutant'),
        ),
        migrations.AlterModelTable(
            name='foreignkeydefinition',
            table=None,
        ),
        migrations.AlterModelTable(
            name='manytomanyfielddefinition',
            table=None,
        ),
    ]
