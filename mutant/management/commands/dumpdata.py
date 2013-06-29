from __future__ import unicode_literals

from django.core.management.commands.dumpdata import Command as BaseCommand

from ...models import ModelDefinition


class Command(BaseCommand):
    """
    `dumpdata` command override that makes sure to load all required mutable
    models in the cache prior to dumping.
    """

    def handle(self, *app_labels, **options):
        model_defs = ModelDefinition.objects.all()

        # Filter out non needed model definitions when some are specified.
        if app_labels:
            model_defs = model_defs.filter(
                app_label__in=set(
                    app_label.split('.')[0] for app_label in app_labels
                )
            )

        # Generate model class associated with model classes.
        for model_def in model_defs:
            model_def.model_class()

        return super(Command, self).handle(*app_labels, **options)
