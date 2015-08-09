from __future__ import unicode_literals

from .postgresql_psycopg2 import *  # NOQA

DATABASES['default']['ENGINE'] = 'django.contrib.gis.db.backends.postgis'

INSTALLED_APPS.extend([
    'django.contrib.gis',
    'mutant.contrib.geo',
])
