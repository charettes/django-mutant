#!/usr/bin/env python
from __future__ import unicode_literals

import argparse
import os
import sys

from django.conf import settings


class MongoRouter(object):
    def _db_for(self, model, **hints):
        from mutant.db.models import MutableModel
        if issubclass(model, MutableModel):
            return 'mongo'
        else:
            return 'default'

    db_for_read = _db_for
    db_for_write = _db_for

    def allow_syncdb(self, db, model):
        return self._db_for(model) == db


DEFAULT_SETTINGS = {
    'SECRET_KEY': 'secret',
    'INSTALLED_APPS': [
        'django.contrib.auth', # This is needed because of django bug
        'django.contrib.contenttypes',
        'south',
        'polymodels',
        'mutant',
        'mutant.contrib.boolean',
        'mutant.contrib.temporal',
        'mutant.contrib.file',
        'mutant.contrib.numeric',
        'mutant.contrib.text',
        'mutant.contrib.web',
        'mutant.contrib.related',
    ],
    'SKIP_SOUTH_TESTS': False
}


ENGINE_SETTINGS = {
    'sqlite3': {
        'DATABASES': {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        }
    },
    'postgresql': {
        'DATABASES': {
            'default': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME': 'mutant',
                'USER': 'postgres',
            }
        }
    },
    'postgis': {
        'DATABASES': {
            'default': {
                'ENGINE': 'django.contrib.gis.db.backends.postgis',
                'NAME': 'mutant',
                'USER': 'postgres',
            }
        },
        'INSTALLED_APPS': DEFAULT_SETTINGS['INSTALLED_APPS'] + [
            'django.contrib.gis',
            'mutant.contrib.geo',
        ]
    },
    'mongodb': {
        'DATABASES': {
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
        },
        'DATABASE_ROUTERS': ('runtests.MongoRouter',),
        'SOUTH_DATABASE_ADAPTERS': {
            'mongo': 'django_mongodb_engine.south_adapter'
        },
        'INSTALLED_APPS': DEFAULT_SETTINGS['INSTALLED_APPS'][0:-1] + [
            'django_mongodb_engine',
            'djangotoolbox',
            'mutant.contrib.nonrel',
        ]
    },
}


DEFAULT_TEST_LABELS = [
    'mutant',
    'boolean',
    'temporal',
    'file',
    'numeric',
    'related',
    'text',
    'web',
    'south',
    'polymodels',
]

def main(engine, user, verbosity, failfast, test_labels):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'runtests'
    try:
        engine_settings = ENGINE_SETTINGS[engine]
    except KeyError:
        raise Exception("Unconfigured engine '%s'" % engine)
    if not test_labels:
        test_labels = DEFAULT_TEST_LABELS
        if engine == 'postgis':
            test_labels.append('geo')
        elif engine == 'mongodb':
            test_labels.remove('related')
            test_labels.append('nonrel')
    options = dict(DEFAULT_SETTINGS, **engine_settings)
    if user:
        options['DATABASES']['default']['USER'] = user
    settings.configure(**options)
    from django.test.utils import get_runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=verbosity, interactive=False,
                             failfast=failfast)
    failures = test_runner.run_tests(test_labels)
    sys.exit(failures)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--failfast', action='store_true', default=False,
                        dest='failfast')
    parser.add_argument('--engine', default='sqlite3')
    parser.add_argument('--user')
    parser.add_argument('--verbosity', default=1)
    parser.add_argument('test_labels', nargs='*')
    args = parser.parse_args()
    main(args.engine, args.user, args.verbosity,
         args.failfast, args.test_labels)
