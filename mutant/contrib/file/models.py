
from django.db.models import fields
from django.utils.translation import ugettext_lazy as _

from ..text.models import CharFieldDefinition
from ...db.fields.python import DirectoryPathField, RegExpStringField


path_help_text = _(u'The absolute filesystem path to a directory from which '
                   u'this field should get its choices.')
match_help_text = _(u'A regular expression used to filter filenames.')
recursive_help_text = _(u'Specifies whether all subdirectories of '
                        u'path should be included')

class FilePathFieldDefinition(CharFieldDefinition):
    
    path = DirectoryPathField(_(u'path'), max_length=100,
                              help_text=path_help_text)
    match = RegExpStringField(_(u'match'), max_length=100,
                              blank=True, null=True, help_text=match_help_text)
    recursive = fields.BooleanField(_(u'recursive'), default=False,
                                    help_text=recursive_help_text)
    
    class Meta:
        app_label = 'mutant'
        verbose_name = _(u'file path field')
        verbose_name_plural = _(u'file paths fields')
        defined_field_class = fields.FilePathField
        defined_field_options = ('path', 'match', 'recursive')
        defined_field_category = _(u'file')
