
from django.utils.encoding import force_unicode
from django.utils.functional import lazy


# TODO: Remove when support for django 1.4 is dropped
def get_concrete_model(model):
    """
    Prior to django r17573 (django 1.4), `proxy_for_model` returned the
    actual concrete model of a proxy and there was no `concrete_model`
    property so we try to fetch the `concrete_model` from the opts
    and fallback to `proxy_for_model` if it's not defined.
    """
    return getattr(model._meta, 'concrete_model', model._meta.proxy_for_model)

def popattr(obj, attr, default):
    """
    Useful for retrieving an object attr and removing it if it's part of it's 
    dict while allowing retrieving from subclass.
    i.e.
    class A:
        a = 'a'
    class B(A):
        b = 'b'
    >>> popattr(B, 'a', None)
    'a'
    >>> A.a
    'a'
    """
    val = getattr(obj, attr, default)
    try:
        delattr(obj, attr)
    except AttributeError:
        pass
    return val

def _string_format(string, *args, **kwargs):
    if args:
        return string % tuple(force_unicode(s) for s in args)
    elif kwargs:
        return string % dict((k, force_unicode(v)) for k, v in kwargs.iteritems())
lazy_string_format = lazy(_string_format, unicode)
