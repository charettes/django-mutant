from __future__ import unicode_literals

from django.db.models import fields
from django.utils.translation import ugettext_lazy as _

from ...db.fields.python import DirectoryPathField, RegExpStringField
from ...models.field.managers import FieldDefinitionManager
from ..text.models import CharFieldDefinition

path_help_text = _('The absolute filesystem path to a directory from which '
                   'this field should get its choices.')
match_help_text = _('A regular expression used to filter filenames.')
recursive_help_text = _('Specifies whether all subdirectories of '
                        'path should be included')


class FilePathFieldDefinition(CharFieldDefinition):
    path = DirectoryPathField(_('path'), max_length=100,
                              help_text=path_help_text)
    match = RegExpStringField(_('match'), max_length=100,
                              blank=True, null=True, help_text=match_help_text)
    recursive = fields.BooleanField(_('recursive'), default=False,
                                    help_text=recursive_help_text)

    objects = FieldDefinitionManager()

    class Meta:
        app_label = 'file'
        defined_field_class = fields.FilePathField
        defined_field_options = ('path', 'match', 'recursive')
        defined_field_category = _('File')
