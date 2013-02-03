from __future__ import unicode_literals

from . import *


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
    'mongo': {
        'ENGINE': 'django_mongodb_engine',
        'NAME': 'mutant',
        'OPTIONS': {
            'OPERATIONS': {
                'save': {'safe': True},
            }
        }
    }
}

DATABASE_ROUTERS = ('tests.routers.MongoDBRouter',)

SOUTH_DATABASE_ADAPTERS = {
    'mongo': 'django_mongodb_engine.south_adapter'
}

INSTALLED_APPS.extends([
    'django_mongodb_engine',
    'djangotoolbox',
    'mutant.contrib.nonrel',
])

TEST_DEFAULT_LABELS.remove('related')
TEST_DEFAULT_LABELS.append('nonrel')

COVERAGE_MODULE_EXCLUDES.remove('mutant.contrib.nonrel')
COVERAGE_MODULE_EXCLUDES.append('mutant.contrib.related')