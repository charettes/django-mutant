from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django.utils.unittest.case import TestCase

from mutant.db.fields.translation import LazilyTranslatedField


class LazilyTranslatedFieldTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.field = LazilyTranslatedField()
        return super(LazilyTranslatedFieldTest, cls).setUpClass()

    def test_to_python(self):
        self.assertIsNone(self.field.to_python(None))
        self.assertEqual(self.field.to_python(_('hello')), _('hello'))
        self.assertEqual(self.field.to_python('hello'), _('hello'))
        self.assertEqual(self.field.to_python('hello'), _('hello'))
        self.assertEqual(self.field.to_python(1), _('1'))

    def test_get_prep_value(self):
        self.assertIsNone(self.field.get_prep_value(None))
        self.assertEqual(self.field.get_prep_value(_('hello')), 'hello')
        self.assertEqual(self.field.get_prep_value('hello'), 'hello')
        self.assertEqual(self.field.get_prep_value('hello'), 'hello')
        self.assertEqual(self.field.get_prep_value(1), '1')
