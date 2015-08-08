from __future__ import unicode_literals

import logging
from optparse import make_option

from django.test.runner import DiscoverRunner

from mutant import logger


class MutantTestSuiteRunner(DiscoverRunner):
    option_list = (
        make_option(
            '-l', '--logger-level',
            dest='logger_level',
            help='Set the level of the `mutant` logger.'
        ),
    )

    def __init__(self, logger_level, **kwargs):
        super(MutantTestSuiteRunner, self).__init__(**kwargs)
        if logger_level:
            logger.setLevel(logger_level)
            logger.addHandler(logging.StreamHandler())
