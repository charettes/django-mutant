from __future__ import unicode_literals

from operator import attrgetter

import django

get_related_model = attrgetter('related_model' if django.VERSION >= (1, 8) else 'model')


if django.VERSION >= (1, 8):
    def get_remote_field_accessor_name(field):
        return get_remote_field(field).get_accessor_name()

    def get_reverse_fields(opts):
        return opts._get_fields(forward=False, reverse=True, include_hidden=True)

    def clear_opts_related_cache(model_class):
        opts = model_class._meta
        children = [
            related_object.related_model
            for related_object in opts.related_objects if related_object.parent_link
        ]
        opts._expire_cache()
        for child in children:
            clear_opts_related_cache(child)
else:
    def get_remote_field_accessor_name(field):
        return field.related.get_accessor_name()

    def get_reverse_fields(opts):
        return opts.get_all_related_objects(include_hidden=True)

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

get_remote_field = attrgetter('remote_field' if django.VERSION >= (1, 9) else 'rel')
