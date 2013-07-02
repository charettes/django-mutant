from __future__ import unicode_literals

from django.forms.forms import Form
from django.test.testcases import TestCase

from mutant.forms import FieldDefinitionTypeField
from mutant.models.field import FieldDefinition


class FieldDefinitionTypeFieldTest(TestCase):
    def test_invalid_fd(self):
        with self.assertRaisesMessage(TypeError,
                                      'is not a subclass of FieldDefinitionBase'):
            FieldDefinitionTypeField((FieldDefinitionTypeField,))

    def test_valid_fd(self):
        field = FieldDefinitionTypeField((FieldDefinition,))
        custom_field_ct = FieldDefinition.get_content_type()
        self.assertTrue(field.valid_value(FieldDefinition))
        self.assertTrue(field.valid_value(custom_field_ct))
        self.assertTrue(field.valid_value(custom_field_ct.pk))

    def test_form_validation(self):
        custom_field_ct = FieldDefinition.get_content_type()

        class CustomModelForm(Form):
            field_type = FieldDefinitionTypeField((FieldDefinition,))
        data = {'field_type': custom_field_ct.pk}
        form = CustomModelForm(data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['field_type'], custom_field_ct)
