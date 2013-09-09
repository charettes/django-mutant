from __future__ import unicode_literals

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test.testcases import TestCase
from django.utils.translation import ugettext

from mutant.forms import FieldDefinitionTypeField
from mutant.models.field import FieldDefinition

from .models import CustomFieldDefinition, FieldDefinitionModel


class FieldDefinitionTypeFieldTest(TestCase):
    def setUp(self):
        self.field_definition_ct = FieldDefinition.get_content_type()
        self.custom_field_ct = CustomFieldDefinition.get_content_type()
        self.content_type_ct = ContentType.objects.get_for_model(ContentType)
        self.field_types = ContentType.objects.filter(
            **FieldDefinition.subclasses_lookup('pk')
        )

    def test_invalid_field_definitions(self):
        with self.assertRaisesMessage(
            TypeError, 'is not a subclass of `FieldDefinition`'):
            FieldDefinitionTypeField(
                self.field_types, field_definitions=[FieldDefinitionTypeField]
            )

    def test_valid_value(self):
        field = FieldDefinitionTypeField(self.field_types)
        self.assertEqual(
            field.to_python(self.field_definition_ct.pk),
            self.field_definition_ct
        )
        self.assertEqual(
            field.to_python(self.custom_field_ct.pk),
            self.custom_field_ct
        )
        with self.assertRaises(ValidationError):
            field.to_python(self.content_type_ct.pk)

    def test_field_definitions_valid_value(self):
        field = FieldDefinitionTypeField(
            self.field_types, field_definitions=[CustomFieldDefinition]
        )
        with self.assertRaises(ValidationError):
            field.to_python(self.field_definition_ct.pk)
        self.assertEqual(
            field.to_python(self.custom_field_ct.pk),
            self.custom_field_ct
        )
        with self.assertRaises(ValidationError):
            field.to_python(self.content_type_ct.pk)

    def test_form_validation(self):
        custom_field_ct = CustomFieldDefinition.get_content_type()

        class CustomModelForm(forms.Form):
            field_type = FieldDefinitionTypeField(self.field_types)
        form = CustomModelForm({'field_type': self.custom_field_ct.pk})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['field_type'], custom_field_ct)

    def test_model_form_validation(self):
        form_cls = forms.models.modelform_factory(FieldDefinitionModel)

        form = form_cls({'field_type': self.field_definition_ct.pk})
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data['field_type'], self.field_definition_ct
        )

        form = form_cls({'field_type': self.custom_field_ct.pk})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['field_type'], self.custom_field_ct)

        form = form_cls({'field_type': self.content_type_ct.pk})
        self.assertFalse(form.is_valid())

    def test_group_by_category(self):
        field = FieldDefinitionTypeField(
            ContentType.objects.filter(pk__in=[
                self.field_definition_ct.pk, self.custom_field_ct.pk
            ]).order_by('pk'), group_by_category=True, empty_label=None
        )
        self.assertEqual(
            field.choices, [
                (self.field_definition_ct.pk, 'None'),
                (ugettext('Custom category'), (
                    (self.custom_field_ct.pk, ugettext('Custom description')),
                ))
            ]
        )
