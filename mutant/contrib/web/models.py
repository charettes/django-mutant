from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db.models import fields
from django.utils.translation import ugettext_lazy as _

from ...models import FieldDefinitionManager
from ..text.models import CharFieldDefinition


class _WebMeta:
    defined_field_category = _('Web')


class EmailFieldDefinition(CharFieldDefinition):
    class Meta(_WebMeta):
        app_label = 'web'
        proxy = True
        defined_field_class = fields.EmailField


class URLFieldDefinition(CharFieldDefinition):
    class Meta(_WebMeta):
        app_label = 'web'
        proxy = True
        defined_field_class = fields.URLField


class SlugFieldDefinition(CharFieldDefinition):
    class Meta(_WebMeta):
        app_label = 'web'
        proxy = True
        defined_field_class = fields.SlugField
        defined_field_description = _('slug')


class IPAddressFieldDefinition(CharFieldDefinition):
    class Meta(_WebMeta):
        app_label = 'web'
        proxy = True
        defined_field_class = fields.IPAddressField


protocol_help_text = _('Limits valid inputs to the specified protocol.')
unpack_ipv4_help_text = _('Unpacks IPv4 mapped addresses like '
                          '``::ffff::192.0.2.1`` to ``192.0.2.1``')


class GenericIPAddressFieldDefinition(CharFieldDefinition):
    PROTOCOL_BOTH = 'both'
    PROTOCOL_IPV4 = 'IPv4'
    PROTOCOL_IPV6 = 'IPv6'

    PROTOCOL_CHOICES = (
        (PROTOCOL_BOTH, _('both')),
        (PROTOCOL_IPV4, _('IPv4')),
        (PROTOCOL_IPV6, _('IPv6'))
    )

    protocol = fields.CharField(
        _('protocol'), max_length=4,
        choices=PROTOCOL_CHOICES, default=PROTOCOL_BOTH
    )
    unpack_ipv4 = fields.BooleanField(_('unpack ipv4'), default=False)

    objects = FieldDefinitionManager()

    class Meta(_WebMeta):
        app_label = 'web'
        defined_field_class = fields.GenericIPAddressField
        defined_field_options = ('protocol', 'unpack_ipv4',)
        defined_field_description = _('generic IP address')

    def clean(self):
        if self.unpack_ipv4 and self.procotol != 'both':
            msg = _("Can only be used when ``protocol`` is set to 'both'.")
            raise ValidationError({'unpack_ipv4': msg})
