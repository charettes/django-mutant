
from ...test.testcases import FieldDefinitionTestMixin
from ...tests.models.utils import BaseModelDefinitionTestCase

from .models import (EmailFieldDefinition, IPAddressFieldDefinition,
    SlugFieldDefinition, URLFieldDefinition)


class EmailFieldDefinitionTest(FieldDefinitionTestMixin,
                               BaseModelDefinitionTestCase):
    field_definition_cls = EmailFieldDefinition
    field_values = ('guido@python.org', 'god@heaven.com')
    
class IPAddressFieldDefinitionTest(FieldDefinitionTestMixin,
                                   BaseModelDefinitionTestCase):
    field_definition_cls = IPAddressFieldDefinition
    field_defintion_init_kwargs = {'default': '192.168.1.1'}
    field_values = ('127.0.0.1', '82.94.164.162')

class SlugFieldDefinitionTest(FieldDefinitionTestMixin,
                              BaseModelDefinitionTestCase):
    field_definition_cls = SlugFieldDefinition
    field_values = (
        'an-awesome-slug_-_-',
        '2012-4-7-so-late'
    )
    
class URLFieldDefinitionTest(FieldDefinitionTestMixin,
                             BaseModelDefinitionTestCase):
    field_definition_cls = URLFieldDefinition
    field_values = (
        'https://github.com/charettes/django-mutant',
        'http://travis-ci.org/#!/charettes/django-mutant',
    )

try:
    from .models import GenericIPAddressFieldDefinition
except ImportError:
    pass
else:
    class GenericIPAddressFieldDefinitionTest(FieldDefinitionTestMixin,
                                              BaseModelDefinitionTestCase):
        field_definition_cls = GenericIPAddressFieldDefinition
        field_values = (
            '127.0.0.1',
            '2001:db8:85a3::8a2e:370:7334'
        )
