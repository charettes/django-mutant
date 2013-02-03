from __future__ import unicode_literals

from .postgresql_psycopg2 import *


DATABASES['default']['ENGINE'] = 'django.contrib.gis.db.backends.postgis'

INSTALLED_APPS.extend([
    'django.contrib.gis',
    'mutant.contrib.geo',
])

TEST_DEFAULT_LABELS.append('geo')

COVERAGE_MODULE_EXCLUDES.remove('mutant.contrib.geo')