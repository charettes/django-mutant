
from django.conf import settings

MIXINS_CLASSES = getattr(settings, 'DYNAMODEF_MIXINS_CLASSES', ())