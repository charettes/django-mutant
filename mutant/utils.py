from __future__ import unicode_literals

from contextlib import contextmanager
from copy import deepcopy
from itertools import chain, groupby
import imp
from operator import itemgetter

import django
from django.db import connections, models, router
from django.db.models.loading import cache as app_cache
from django.utils import six
from django.utils.datastructures import SortedDict
from django.utils.encoding import force_text
from django.utils.functional import lazy


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
        return string % tuple(force_text(s) for s in args)
    elif kwargs:
        return string % dict((k, force_text(v)) for k, v in kwargs.items())
lazy_string_format = lazy(_string_format, six.text_type)


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
                unreference_model(model)
                return model


def unreference_model(model):
    opts = model._meta
    for field, field_model in chain(opts.get_fields_with_model(),
                                    opts.get_m2m_with_model()):
        rel = field.rel
        if field_model is None and rel:
            to = rel.to
            if isinstance(to, models.base.ModelBase):
                clear_opts_related_cache(to)
                rel_is_hidden = rel.is_hidden()
                # An accessor is added to related classes if they are not
                # hidden. However o2o fields *always* add an accessor
                # even if the relationship is hidden.
                o2o = isinstance(field, models.OneToOneField)
                if not rel_is_hidden or o2o:
                    try:
                        delattr(to, field.related.get_accessor_name())
                    except AttributeError:
                        # Hidden related names are not respected for o2o
                        # thus a tenant models with a o2o pointing to
                        # a non-tenant one would have a class for multiple
                        # tenant thus the attribute might be attempted
                        # to be deleted multiple times.
                        if not (o2o and rel_is_hidden):
                            raise


def _app_cache_deepcopy(obj):
    """
    An helper that correctly deepcopy model cache state
    """
    if isinstance(obj, dict):
        return dict((_app_cache_deepcopy(key), _app_cache_deepcopy(val))
                    for key, val in obj.items())
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
            yield (grp, tuple(
                (choice['value'], choice['label']) for choice in choices)
            )


_opts_related_cache_attrs = [
    '_related_objects_cache',
    '_related_objects_proxy_cache',
    '_related_many_to_many_cache',
    '_name_map',
]


def clear_opts_related_cache(model_class):
    """
    Clear the specified model and its children opts related cache.
    """
    opts = model_class._meta
    children = [
        related_object.model
        for related_object in opts.get_all_related_objects()
        if related_object.field.rel.parent_link
    ]
    for attr in _opts_related_cache_attrs:
        try:
            delattr(opts, attr)
        except AttributeError:
            pass
    for child in children:
        clear_opts_related_cache(child)
