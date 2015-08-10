from __future__ import unicode_literals


# TODO: Remove when dropping support for Django 1.7
def patch_model_option_verbose_name_raw():
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
