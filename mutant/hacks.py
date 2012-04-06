
# Field instances cannot be compared to other objects because of attribute
# presence assumptions in it's __cmp__ method. To allow full_clean we must
# override the item_field __cmp__ method to return NotImplemented if the
# object it's compared to isn't a Field instance. Let's monkey patch it!
# see https://code.djangoproject.com/ticket/17851
def patch_db_field_compare():
    from django.db.models.fields import Field
    try:
        assert Field() != None
    except AttributeError:
        del Field.__cmp__
        def _Field__lt__(self, other):
            if isinstance(other, Field):
                return self.creation_counter < other.creation_counter
            return NotImplemented
        Field.__lt__ = _Field__lt__
        assert Field() != None
