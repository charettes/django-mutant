from __future__ import unicode_literals

from .test_base import *


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'mutant',
        'USER': 'postgres'
    }
}