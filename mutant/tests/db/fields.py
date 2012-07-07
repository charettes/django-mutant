
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
        self.assertEqual(self.field.to_python(_(u'hello')), _(u'hello'))
        self.assertEqual(self.field.to_python('hello'), _(u'hello'))
        self.assertEqual(self.field.to_python(u'hello'), _(u'hello'))
        self.assertEqual(self.field.to_python(1), _(u'1'))

    def test_get_prep_value(self):
        self.assertIsNone(self.field.get_prep_value(None))
        self.assertEqual(self.field.get_prep_value(_(u'hello')), u'hello')
        self.assertEqual(self.field.get_prep_value('hello'), u'hello')
        self.assertEqual(self.field.get_prep_value(u'hello'), u'hello')
        self.assertEqual(self.field.get_prep_value(1), u'1')
