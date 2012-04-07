
def patch_db_field_compare():
    """
    Field instances cannot be compared to other objects because of attribute
    presence assumptions in it's __cmp__ method. To allow full_clean we must
    override the item_field __cmp__ method to return NotImplemented if the
    object it's compared to isn't a Field instance. Let's monkey patch it!
    see https://code.djangoproject.com/ticket/17851
    """
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

def patch_postgis_bad_geomery_escape():
    """
    When using django 1.3.X with PostgreSQL 9.1 some geometry can be badly
    escaped. Monkey patch PostGISAdapter to fix this issue.
    see https://code.djangoproject.com/ticket/16778
    """
    import django
    if django.VERSION < (1, 4):
        from django.db import connections
        postgis_engine = 'django.contrib.gis.db.backends.postgis'
        if any(connection.settings_dict['ENGINE'] == postgis_engine
               for connection in connections.all()):
            from psycopg2 import Binary
            from django.contrib.gis.db.backends.postgis.adapter import PostGISAdapter
            
            PostGISAdapter__init__ = PostGISAdapter.__init__
            def _PostGISAdapter__init__(self, *args, **kwargs):
                PostGISAdapter__init__(self, *args, **kwargs)
                self._adapter = Binary(self.ewkb)
            PostGISAdapter.__init__ = _PostGISAdapter__init__
            
            def _PostGISAdapter_prepare(self, conn):
                self._adapter.prepare(conn)
            PostGISAdapter.prepare = _PostGISAdapter_prepare
            
            def _PostGISAdapter_getquoted(self):
                return 'ST_GeomFromEWKB(%s)' % self._adapter.getquoted()
            PostGISAdapter.getquoted = _PostGISAdapter_getquoted
