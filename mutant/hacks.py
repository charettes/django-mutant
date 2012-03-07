
# Field instances cannot be compared to other objects because of attribute
# presence assumptions in it's __cmp__ method. To allow full_clean we must
# override the item_field __cmp__ method to return NotImplemented if the
# object it's compared to isn't a Field instance. Let's monkey patch it!
# see https://code.djangoproject.com/ticket/17851
from django.db.models.fields import Field
try:
    assert Field() != None
except AttributeError:
    def _Field__cmp__(self, other):
        if isinstance(other, Field):
            return cmp(self.creation_counter, other.creation_counter)
        return NotImplemented
    Field.__cmp__ = _Field__cmp__
    assert Field() != None