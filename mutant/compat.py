from __future__ import unicode_literals

from contextlib import contextmanager
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
            for related_object in opts.__dict__.get('related_objects', []) if related_object.parent_link
        ]
        opts._expire_cache()
        for child in children:
            clear_opts_related_cache(child)

    from django.db.migrations.state import StateApps
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
        if hasattr(opts, '_related_objects_cache'):
            children = [
                related_object.model
                for related_object in opts.get_all_related_objects()
                if related_object.field.rel.parent_link
            ]
        else:
            children = []
        for attr in _opts_related_cache_attrs:
            try:
                delattr(opts, attr)
            except AttributeError:
                pass
        for child in children:
            clear_opts_related_cache(child)

    from django.apps.registry import Apps
    from django.db.migrations.state import InvalidBasesError

    class StateApps(Apps):
        def __init__(self, *args, **kwargs):
            super(StateApps, self).__init__([])

        @contextmanager
        def bulk_update(self):
            # Avoid clearing each model's cache for each change. Instead, clear
            # all caches when we're finished updating the model instances.
            ready = self.ready
            self.ready = False
            try:
                yield
            finally:
                self.ready = ready
                self.clear_cache()

        def get_model(self, app_label, model_name=None):
            if model_name is None:
                app_label, model_name = app_label.split('.')
            return self.all_models[app_label][model_name]

        def render_multiple(self, model_states):
            # We keep trying to render the models in a loop, ignoring invalid
            # base errors, until the size of the unrendered models doesn't
            # decrease by at least one, meaning there's a base dependency loop/
            # missing base.
            if not model_states:
                return
            # Prevent that all model caches are expired for each render.
            with self.bulk_update():
                unrendered_models = model_states
                while unrendered_models:
                    new_unrendered_models = []
                    for model in unrendered_models:
                        try:
                            model.render(self)
                        except InvalidBasesError:
                            new_unrendered_models.append(model)
                    if len(new_unrendered_models) == len(unrendered_models):
                        raise InvalidBasesError(
                            "Cannot resolve bases for %r\nThis can happen if you are inheriting models from an "
                            "app with migrations (e.g. contrib.auth)\n in an app with no migrations; see "
                            "https://docs.djangoproject.com/en/%s/topics/migrations/#dependencies "
                            "for more" % (new_unrendered_models, '1.7')
                        )
                    unrendered_models = new_unrendered_models

get_remote_field = attrgetter('remote_field' if django.VERSION >= (1, 9) else 'rel')


if django.VERSION >= (1, 9):
    def get_remote_field_model(field):
        model = getattr(field, 'model', None)
        if model:
            return field.remote_field.model
        else:
            return field.related_model
else:
    def get_remote_field_model(field):
        return getattr(getattr(field, 'rel', None), 'to', None)
