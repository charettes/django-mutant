# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import functools

from django.db import migrations


def _update_field_def_cts_app_label(from_app_label, to_app_label, apps, schema_editor):
    cts = apps.get_model('contenttypes', 'contenttype').objects
    cts.filter(
        app_label=from_app_label, model='filepathfielddefinition'
    ).update(app_label=to_app_label)


class Migration(migrations.Migration):

    dependencies = [
        ('file', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            functools.partial(_update_field_def_cts_app_label, 'mutant', 'file'),
            functools.partial(_update_field_def_cts_app_label, 'file', 'mutant'),
        ),
        migrations.AlterModelTable(
            name='filepathfielddefinition',
            table=None,
        ),
    ]
