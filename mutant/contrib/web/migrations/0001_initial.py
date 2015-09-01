# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('text', '0002_update_field_defs_app_label'),
    ]

    operations = [
        migrations.CreateModel(
            name='GenericIPAddressFieldDefinition',
            fields=[
                ('charfielddefinition_ptr', models.OneToOneField(
                    to='text.CharFieldDefinition', on_delete=models.CASCADE, parent_link=True, auto_created=True,
                    primary_key=True, serialize=False
                )),
                ('protocol', models.CharField(default='both', max_length=4, verbose_name='protocol', choices=[('both', 'both'), ('IPv4', 'IPv4'), ('IPv6', 'IPv6')])),
                ('unpack_ipv4', models.BooleanField(default=False, verbose_name='unpack ipv4')),
            ],
            options={
                'db_table': 'mutant_genericipaddressfielddefinition',
            },
            bases=('text.charfielddefinition',),
        ),
        migrations.CreateModel(
            name='EmailFieldDefinition',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('text.charfielddefinition',),
        ),
        migrations.CreateModel(
            name='IPAddressFieldDefinition',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('text.charfielddefinition',),
        ),
        migrations.CreateModel(
            name='SlugFieldDefinition',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('text.charfielddefinition',),
        ),
        migrations.CreateModel(
            name='URLFieldDefinition',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('text.charfielddefinition',),
        ),
    ]
