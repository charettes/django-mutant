from __future__ import unicode_literals

from . import *  # NOQA


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'mutant',
    }
}
