from __future__ import unicode_literals

from collections import defaultdict
from contextlib import contextmanager
from copy import deepcopy
from itertools import chain, groupby
from operator import itemgetter

from django.apps import AppConfig, apps
from django.db import connections, models, router
from django.utils import six
from django.utils.encoding import force_text
from django.utils.functional import lazy

from .compat import get_remote_field, get_remote_field_model


def allow_migrate(model):
    for db in connections:
        if router.allow_migrate(db, model):
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
def apps_lock():
    # The registry lock is not re-entrant so we must avoid acquiring it
    # during the initialization phase in order to prevent deadlocks.
    if apps.ready:
        with apps._lock:
            yield
    else:
        yield


def remove_from_app_cache(model_class, quiet=False):
    opts = model_class._meta
    apps = opts.apps
    app_label, model_name = opts.app_label, opts.model_name
    with apps_lock():
        try:
            model_class = apps.app_configs[app_label].models.pop(model_name)
        except KeyError:
            if not quiet:
                raise ValueError("%r is not cached" % model_class)
        apps.clear_cache()
        unreference_model(model_class)
    return model_class


def get_foward_fields(opts):
    return chain(
        opts.fields,
        opts.many_to_many
    )


def get_reverse_fields(opts):
    return opts._get_fields(forward=False, reverse=True, include_hidden=True)


def clear_opts_related_cache(model_class):
    opts = model_class._meta
    children = [
        related_object.related_model
        for related_object in opts.__dict__.get('related_objects', []) if related_object.parent_link
    ]
    opts._expire_cache()
    for child in children:
        clear_opts_related_cache(child)


def unreference_model(model):
    for field in get_foward_fields(model._meta):
        remote_field = get_remote_field(field)
        if field.model is model and remote_field:
            remote_field_model = get_remote_field_model(field)
            if isinstance(remote_field_model, models.base.ModelBase):
                clear_opts_related_cache(remote_field_model)
                rel_is_hidden = remote_field.is_hidden()
                # An accessor is added to related classes if they are not
                # hidden. However o2o fields *always* add an accessor
                # even if the relationship is hidden.
                o2o = isinstance(field, models.OneToOneField)
                if not rel_is_hidden or o2o:
                    try:
                        delattr(remote_field_model, get_remote_field(field).get_accessor_name())
                    except AttributeError:
                        # Hidden related names are not respected for o2o
                        # thus a tenant models with a o2o pointing to
                        # a non-tenant one would have a class for multiple
                        # tenant thus the attribute might be attempted
                        # to be deleted multiple times.
                        if not (o2o and rel_is_hidden):
                            raise


class Empty(object):
    pass


def _app_cache_deepcopy(obj):
    """
    An helper that correctly deepcopy model cache state
    """
    if isinstance(obj, defaultdict):
        return deepcopy(obj)
    elif isinstance(obj, dict):
        return type(obj)((_app_cache_deepcopy(key), _app_cache_deepcopy(val)) for key, val in obj.items())
    elif isinstance(obj, list):
        return list(_app_cache_deepcopy(val) for val in obj)
    elif isinstance(obj, AppConfig):
        app_conf = Empty()
        app_conf.__class__ = AppConfig
        app_conf.__dict__ = _app_cache_deepcopy(obj.__dict__)
        return app_conf
    return obj


@contextmanager
def app_cache_restorer():
    """
    A context manager that restore model cache state as it was before
    entering context.
    """
    state = _app_cache_deepcopy(apps.__dict__)
    try:
        yield state
    finally:
        with apps_lock():
            apps.__dict__ = state
            # Rebind the app registry models cache to
            # individual app config ones.
            for app_conf in apps.get_app_configs():
                app_conf.models = apps.all_models[app_conf.label]
            apps.clear_cache()


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
