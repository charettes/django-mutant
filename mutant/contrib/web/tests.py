from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from mutant.test.testcases import FieldDefinitionTestMixin
from mutant.tests.utils import BaseModelDefinitionTestCase

from .models import (EmailFieldDefinition, GenericIPAddressFieldDefinition,
    IPAddressFieldDefinition, SlugFieldDefinition, URLFieldDefinition)


class WebFieldDefinitionTestMixin(FieldDefinitionTestMixin):
    field_definition_category = _('Web')


class EmailFieldDefinitionTest(WebFieldDefinitionTestMixin,
                               BaseModelDefinitionTestCase):
    field_definition_cls = EmailFieldDefinition
    field_values = ('guido@python.org', 'god@heaven.com')


class IPAddressFieldDefinitionTest(WebFieldDefinitionTestMixin,
                                   BaseModelDefinitionTestCase):
    field_definition_cls = IPAddressFieldDefinition
    field_definition_init_kwargs = {'default': '192.168.1.1'}
    field_values = ('127.0.0.1', '82.94.164.162')


class SlugFieldDefinitionTest(WebFieldDefinitionTestMixin,
                              BaseModelDefinitionTestCase):
    field_definition_cls = SlugFieldDefinition
    field_values = (
        'an-awesome-slug_-_-',
        '2012-4-7-so-late'
    )


class URLFieldDefinitionTest(WebFieldDefinitionTestMixin,
                             BaseModelDefinitionTestCase):
    field_definition_cls = URLFieldDefinition
    field_values = (
        'https://github.com/charettes/django-mutant',
        'http://travis-ci.org/#!/charettes/django-mutant',
    )


class GenericIPAddressFieldDefinitionTest(WebFieldDefinitionTestMixin,
                                          BaseModelDefinitionTestCase):
    field_definition_cls = GenericIPAddressFieldDefinition
    field_values = (
        '127.0.0.1',
        '2001:db8:85a3::8a2e:370:7334'
    )
