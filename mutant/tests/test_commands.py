from __future__ import unicode_literals

import json
from StringIO import StringIO
from tempfile import NamedTemporaryFile

from django.core.management import call_command
from django.core.serializers.json import Serializer as JSONSerializer

from mutant.models import ModelDefinition
from mutant.test.testcases import ModelDefinitionDDLTestCase
from mutant.utils import remove_from_app_cache
from django.core.serializers.base import DeserializationError


class DataCommandTestCase(ModelDefinitionDDLTestCase):
    def setUp(self):
        self.model_def = ModelDefinition.objects.create(
            app_label='mutant', object_name='Model'
        )
        self.model_cls = self.model_def.model_class()

    def tearDown(self):
        if self.model_def.pk:
            self.model_def.delete()


class DumpDataTestCase(DataCommandTestCase):
    def dump_model_data(self):
        # Make sure to remove the model from the app cache because we're
        # actually testing it's correctly loaded.
        output = StringIO()
        remove_from_app_cache(self.model_cls)
        call_command(
            'dumpdata', str(self.model_def), stdout=output, commit=False
        )
        output.seek(0)
        return json.load(output)

    def test_dump_mutable_models(self):
        """
        Make sure mutable models instances are dumped when calling `dumpdata`.
        """
        self.assertEqual(self.dump_model_data(), [])
        instance = self.model_cls.objects.create()
        self.assertEqual(
            self.dump_model_data(), [{
                'pk': instance.pk,
                'model': str(self.model_def).lower(),
                'fields': {}
            }]
        )


class LoadDataTestCase(DataCommandTestCase):
    def setUp(self):
        super(LoadDataTestCase, self).setUp()
        self.serializer = JSONSerializer()

    def test_load_mutable_models(self):
        """
        Makes sure mutable models instances are correctly loaded when calling
        `loaddata`.
        """
        instance = self.model_cls(pk=1)
        # Make sure to remove the model from the app cache because we're
        # actually testing it's correctly loaded.
        remove_from_app_cache(self.model_cls)
        with NamedTemporaryFile(suffix='.json') as stream:
            self.serializer.serialize([instance], stream=stream)
            stream.seek(0)
            call_command(
                'loaddata', stream.name, stdout=StringIO(), commit=False
            )
        self.assertTrue(self.model_cls.objects.filter(pk=instance.pk).exists())

    def test_invalid_model_idenfitier_raises(self):
        """
        Makes sure an invalid model identifier raises the correct exception.
        """
        instance = self.model_cls(pk=1)
        with NamedTemporaryFile(suffix='.json') as stream:
            self.serializer.serialize([instance], stream=stream)
            stream.seek(0)
            self.model_def.delete()
            with self.assertRaisesMessage(
                    DeserializationError, "Invalid model identifier: 'mutant.model'"):
                call_command(
                    'loaddata', stream.name, stdout=StringIO()
                )
