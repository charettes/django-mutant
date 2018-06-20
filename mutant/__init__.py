from __future__ import unicode_literals

import logging

from .version import get_version

VERSION = (0, 3, 0, 'alpha', 7)

__version__ = get_version(VERSION)

logger = logging.getLogger('mutant')

default_app_config = 'mutant.apps.MutantConfig'
