from __future__ import unicode_literals

import operator

from contextlib import contextmanager
from copy import deepcopy
from itertools import groupby
import imp
from operator import itemgetter

import django
from django.db import connections, router
from django.db.models.loading import cache as app_cache
from django.utils.datastructures import SortedDict
from django.utils.encoding import force_unicode
from django.utils.functional import lazy, LazyObject, new_method_proxy


# TODO: Remove `allow_syncdb` alternative when support for 1.6 is dropped
if django.VERSION >= (1, 7):
    def allow_migrate(model):
        for db in connections:
            if router.allow_migrate(db, model):
                yield db
else:
    def allow_migrate(model):
        for db in connections:
            if router.allow_syncdb(db, model):
                yield db


NOT_PROVIDED = object()


def popattr(obj, attr, default=NOT_PROVIDED):
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
        if default is NOT_PROVIDED:
            raise
    return val


def _string_format(string, *args, **kwargs):
    if args:
        return string % tuple(force_unicode(s) for s in args)
    elif kwargs:
        return string % dict((k, force_unicode(v)) for k, v in kwargs.iteritems())
lazy_string_format = lazy(_string_format, unicode)


def get_db_table(app_label, model):
    return "mutant_%s_%s" % (app_label, model)


@contextmanager
def app_cache_lock():
    try:
        imp.acquire_lock()
        yield
    finally:
        imp.release_lock()


def remove_from_app_cache(model_class):
    opts = model_class._meta
    app_label, model_name = opts.app_label, opts.model_name
    with app_cache_lock():
        app_models = app_cache.app_models.get(app_label, False)
        if app_models:
            model = app_models.pop(model_name, False)
            if model:
                app_cache._get_models_cache.clear()
                return model


def _app_cache_deepcopy(obj):
    """
    An helper that correctly deepcopy model cache state
    """
    if isinstance(obj, dict):
        return dict((_app_cache_deepcopy(key), _app_cache_deepcopy(val))
                    for key, val in obj.iteritems())
    elif isinstance(obj, list):
        return list(_app_cache_deepcopy(val) for val in obj)
    elif isinstance(obj, SortedDict):
        return deepcopy(obj)
    return obj


@contextmanager
def app_cache_restorer():
    """
    A context manager that restore model cache state as it was before
    entering context.
    """
    state = _app_cache_deepcopy(app_cache.__dict__)
    try:
        yield state
    finally:
        with app_cache_lock():
            app_cache.__dict__ = state


group_item_getter = itemgetter('group')


def choices_from_dict(choices):
    for grp, choices in groupby(choices, key=group_item_getter):
        if grp is None:
            for choice in choices:
                yield (choice['value'], choice['label'])
        else:
            yield (grp, tuple((choice['value'], choice['label'])
                                for choice in choices))


_opts_related_cache_attrs = [
    '_related_objects_cache', '_related_objects_proxy_cache',
    '_related_many_to_many_cache', '_name_map'
]


def clear_opts_related_cache(model_class):
    """
    Clear the specified model opts related cache
    """
    opts = model_class._meta
    for attr in _opts_related_cache_attrs:
        try:
            delattr(opts, attr)
        except AttributeError:
            pass

# TODO: Remove when support for 1.5 is dropped
if django.VERSION < (1, 6):
    class LazyObject(LazyObject):
        # Dictionary methods support
        __getitem__ = new_method_proxy(operator.getitem)
        __setitem__ = new_method_proxy(operator.setitem)
        __delitem__ = new_method_proxy(operator.delitem)

        __len__ = new_method_proxy(len)
        __contains__ = new_method_proxy(operator.contains)
