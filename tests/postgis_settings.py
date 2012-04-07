
from test_project.settings import *


DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'mutant_postgis',
        'USER': 'mutant',
        'PASSWORD': 'mutant',
    }
}

INSTALLED_APPS.extend(['django.contrib.gis', 'mutant.contrib.geo'])
