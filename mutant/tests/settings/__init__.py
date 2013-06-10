from __future__ import unicode_literals


SECRET_KEY = 'secret'

INSTALLED_APPS = [
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
]

SKIP_SOUTH_TESTS = False

try:
    import django_coverage
except ImportError:
    pass
else:
    INSTALLED_APPS.append('django_coverage')


TEST_RUNNER = 'mutant.tests.runners.MutantTestSuiteRunner'

TEST_DEFAULT_LABELS = [
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

COVERAGE_MODULE_EXCLUDES = [
    '^(?!mutant)',
    'tests$',
    'locale$',
    'fixtures$',
    'hacks$',
    'mutant.contrib.geo',
    'mutant.contrib.nonrel',
]