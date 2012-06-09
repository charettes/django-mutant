
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

def get_concrete_model(model):
    """
    Prior to django r17573 (django 1.4), `proxy_for_model` returned the
    actual concrete model of a proxy and there was no `concrete_model`
    property so we try to fetch the `concrete_model` from the opts
    and fallback to `proxy_for_model` if it's not defined.
    """
    # TODO: Remove when support for django 1.4 is dropped
    return getattr(model._meta, 'concrete_model', model._meta.proxy_for_model)

def get_real_content_type(model, db=None):
    """
    Prior to #18399 being fixed there was no way to retrieve `ContentType`
    of proxy models. This is a shim that tries to use the newly introduced
    flag and fallback to another method.
    """
    # TODO: Remove when support for django 1.4 is dropped
    from django.contrib.contenttypes.models import ContentType
    cts = ContentType.objects
    if db:
        cts = cts.db_manager(db)
    try:
        return cts.get_for_model(model, for_concrete_model=False)
    except TypeError:
        opts = model._meta
        app_label = opts.app_label
        object_name = opts.object_name.lower()
        return cts.get_by_natural_key(app_label, object_name)
