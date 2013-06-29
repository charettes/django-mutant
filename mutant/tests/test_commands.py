from __future__ import unicode_literals

import json
from StringIO import StringIO

from django.core.management import call_command

from mutant.tests.models.utils import BaseModelDefinitionTestCase


class DumpDataTestCase(BaseModelDefinitionTestCase):
    def setUp(self):
        super(DumpDataTestCase, self).setUp()
        # Rename app label since only installed apps can be dumped.
        self.model_def.app_label = 'mutant'
        self.model_def.save(update_fields=['app_label'])

    def dump_model(self):
        output = StringIO()
        call_command(
            'dumpdata', str(self.model_def), stdout=output
        )
        output.seek(0)
        return json.load(output)

    def test_dump_mutable_models(self):
        """
        Make sure mutable models are dumped when calling `dumpdata`.
        """
        self.assertEqual(self.dump_model(), [])
        instance = self.model_def.model_class().objects.create()
        self.assertEqual(
            self.dump_model(), [{
                'pk': instance.pk,
                'model': str(self.model_def).lower(),
                'fields': {}
            }]
        )