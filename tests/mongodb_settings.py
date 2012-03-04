
from test_project.settings import *

DATABASES['mongo'] = {
  'ENGINE' : 'django_mongodb_engine',
  'NAME' : 'mutant',
  'OPTIONS': {
    'OPERATIONS': {
      'save' : {'safe' : True},
    }
  }
}

SOUTH_DATABASE_ADAPTERS = {'mongo': 'django_mongodb_engine.south'}

INSTALLED_APPS.extend(['django_mongodb_engine', 'djangotoolbox'])

# FK and M2M are not supported for nonrel db so we make sure to avoid
# loading mutant.contrib.related
INSTALLED_APPS.remove('mutant.contrib.related')

DATABASE_ROUTERS = (
    'mongodb_router.MongoRouter',
)
