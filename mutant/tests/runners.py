from __future__ import unicode_literals
from optparse import make_option

from django.conf import settings
from django.db.utils import DEFAULT_DB_ALIAS
from django.test.simple import DjangoTestSuiteRunner


class MutantTestSuiteRunner(DjangoTestSuiteRunner):
    option_list = (
        make_option('-u', '--db-user',
            dest='db_user',
            help='Database username'),
    )

    def __init__(self, db_user, **kwargs):
        if db_user is not None:
            settings.DATABASES[DEFAULT_DB_ALIAS]['USER'] = db_user
        super(MutantTestSuiteRunner, self).__init__(**kwargs)

    def build_suite(self, test_labels, extra_tests=None, **kwargs):
        if not test_labels:
            test_labels = getattr(settings, 'TEST_DEFAULT_LABELS', test_labels)
        return super(MutantTestSuiteRunner, self).build_suite(test_labels, extra_tests=None, **kwargs)