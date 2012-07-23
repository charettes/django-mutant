from __future__ import unicode_literals


def patch_postgis_bad_geomery_escape():
    """
    When using django 1.3.X with PostgreSQL 9.1 some geometry can be badly
    escaped. Monkey patch PostGISAdapter to fix this issue.
    see https://code.djangoproject.com/ticket/16778
    """
    # TODO: Remove when support for django 1.3 is dropped
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


def patch_db_field_compare():
    """
    Field instances cannot be compared to other objects because of attribute
    presence assumptions in it's __cmp__ method. To allow full_clean we must
    override the item_field __cmp__ method to return NotImplemented if the
    object it's compared to isn't a Field instance. Let's monkey patch it!
    see https://code.djangoproject.com/ticket/17851
    """
    # TODO: Remove when support for django 1.4 is dropped
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


def patch_model_option_verbose_name_raw():
    """
    Until #17763 and all the permission name length issues are fixed we patch
    the `verbose_name_raw` method to return a truncated string in order to
    avoid DatabaseError.
    """
    from django.db.models.options import Options
    verbose_name_raw = Options.verbose_name_raw.fget
    if hasattr(verbose_name_raw, '_patched'):
        return
    def _get_verbose_name_raw(self):
        name = verbose_name_raw(self)
        if len(name) >= 40:
            name = "%s..." % name[0:36]
        return name
    _get_verbose_name_raw.patched = True
    Options.verbose_name_raw = property(_get_verbose_name_raw)
