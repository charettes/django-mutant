from __future__ import unicode_literals

SECRET_KEY = 'secret'

INSTALLED_APPS = [
    'django.contrib.auth',  # This is needed because of django bug
    'django.contrib.contenttypes',
    'polymodels',
    'mutant',
    'tests',
    'mutant.contrib.boolean',
    'mutant.contrib.temporal',
    'mutant.contrib.file',
    'mutant.contrib.numeric',
    'mutant.contrib.text',
    'mutant.contrib.web',
    'mutant.contrib.related',
]

SILENCED_SYSTEM_CHECKS = ['1_7.W001']
