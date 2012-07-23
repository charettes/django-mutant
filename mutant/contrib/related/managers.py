from __future__ import unicode_literals

from ...managers import FilteredQuerysetManager
from ...models import FieldDefinitionManager


class ForeignKeyDefinitionManager(FilteredQuerysetManager,
                                  FieldDefinitionManager):
    pass
