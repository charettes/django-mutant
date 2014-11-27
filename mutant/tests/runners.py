from __future__ import unicode_literals

import logging
from optparse import make_option

from django.conf import settings
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

    def build_suite(self, test_labels, extra_tests=None, **kwargs):
        if not test_labels:
            test_labels = [
                "%s.tests" % app for app in settings.INSTALLED_APPS
                if app.startswith('mutant')
            ]
        return super(MutantTestSuiteRunner, self).build_suite(
            test_labels, extra_tests=None, **kwargs
        )
