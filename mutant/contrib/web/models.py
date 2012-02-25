
from django.core.exceptions import ValidationError
from django.db.models import fields
from django.utils.translation import ugettext_lazy as _

from ..text.models import CharFieldDefinition


class EmailFieldDefinition(CharFieldDefinition):
    
    class Meta:
        app_label = 'mutant'
        proxy = True
        verbose_name = _(u'email field')
        verbose_name_plural = _(u'email fields')
        defined_field_class = fields.EmailField
        defined_field_category = _(u'web')
        
class URLFieldDefinition(CharFieldDefinition):
    
    class Meta:
        app_label = 'mutant'
        proxy = True
        verbose_name = _(u'URL field')
        verbose_name_plural = _(u'URL fields')
        defined_field_class = fields.URLField
        defined_field_category = _(u'web')
        
class SlugFieldDefinition(CharFieldDefinition):
    
    class Meta:
        app_label = 'mutant'
        proxy = True
        verbose_name = _(u'slug field')
        verbose_name_plural = _(u'slug fields')
        defined_field_class = fields.SlugField
        defined_field_category = _(u'web')
        
class IPAddressFieldDefinition(CharFieldDefinition):
    
    class Meta:
        app_label = 'mutant'
        proxy = True
        verbose_name = _(u'IP address field')
        verbose_name_plural = _(u'IP address fields')
        defined_field_class = fields.IPAddressField
        defined_field_category = _(u'web')

# We should eat our own dogfood and
# provide those options as FieldDefinitionOptionChoice initial_data
# fixture
try:
    # Django 1.4+
    GenericIPAddressField = fields.GenericIPAddressField
except AttributeError:
    pass
else:
    PROTOCOL_CHOICES = (('both', _(u'both')),
                        ('IPv4', _(u'IPv4')),
                        ('IPv6', _(u'IPv6')))
    
    protocol_help_text = _(u'Limits valid inputs to the specified protocol.')
    
    unpack_ipv4_help_text = _(u'Unpacks IPv4 mapped addresses like '
                              u'``::ffff::192.0.2.1`` to ``192.0.2.1``')
    
    class GenericIPAddressFieldDefinition(CharFieldDefinition):
        
        protocol = fields.CharField(_(u'protocol'), max_length=4,
                                    choices=PROTOCOL_CHOICES, default='both')
        
        unpack_ipv4 = fields.BooleanField(_(u'unpack ipv4'), default=False)
        
        class Meta:
            app_label = 'mutant'
            verbose_name = _(u'generic IP address field')
            verbose_name_plural = _(u'generic IP address fields')
            defined_field_class = GenericIPAddressField
            defined_field_options = ('protocol', 'unpack_ipv4',)
            defined_field_category = _(u'web')
            
        def clean(self):
            if self.unpack_ipv4 and self.procotol != 'both':
                msg = _(u"Can only be used when ``protocol`` is set to 'both'.")
                raise ValidationError({'unpack_ipv4': msg})
