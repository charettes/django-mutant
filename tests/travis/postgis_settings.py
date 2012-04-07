
from test_project.settings import *


DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'mutant',
        'USER': 'postgres',
    }
}

INSTALLED_APPS.extend(['django.contrib.gis', 'mutant.contrib.geo'])
