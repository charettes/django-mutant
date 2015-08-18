from __future__ import unicode_literals

import datetime
import warnings

from django.test.utils import override_settings
from django.utils.timezone import make_aware, utc
from django.utils.translation import ugettext_lazy as _

from mutant.contrib.temporal.models import (
    DateFieldDefinition, DateTimeFieldDefinition, TimeFieldDefinition,
)
from mutant.test.testcases import FieldDefinitionTestMixin

from .utils import BaseModelDefinitionTestCase


class TemporalFieldDefinitionTestMixin(FieldDefinitionTestMixin):
    field_definition_category = _('Temporal')


class DateFieldDefinitionTest(TemporalFieldDefinitionTestMixin,
                              BaseModelDefinitionTestCase):
    field_definition_cls = DateFieldDefinition
    field_definition_init_kwargs = {'default': datetime.date(1990, 8, 31)}
    field_values = (
        datetime.date.today(),
        datetime.date(1988, 5, 15)
    )


@override_settings(USE_TZ=False)
class NaiveDateTimeFieldDefinitionTest(TemporalFieldDefinitionTestMixin,
                                       BaseModelDefinitionTestCase):
    field_definition_cls = DateTimeFieldDefinition
    field_definition_init_kwargs = {
        'default': datetime.datetime(1990, 8, 31, 23, 46)
    }
    field_values = (
        datetime.datetime(2020, 11, 15, 15, 34),
        datetime.datetime(1988, 5, 15, 15, 30)
    )


@override_settings(USE_TZ=True)
class AwareDateTimeFieldDefinitionTest(TemporalFieldDefinitionTestMixin,
                                       BaseModelDefinitionTestCase):
    field_definition_cls = DateTimeFieldDefinition
    field_definition_init_kwargs = {
        'default': make_aware(datetime.datetime(1990, 8, 31, 23, 46), utc)
    }
    field_values = (
        make_aware(datetime.datetime(2020, 11, 15, 15, 34), utc),
        make_aware(datetime.datetime(1988, 5, 15, 15, 30), utc)
    )

    def test_create_with_naive_default(self):
        """Makes sure creating a DateTimeField with a naive default while
        timezone support is turned on correctly raise a warning instead
        of throwing an exception. refs #23"""
        naive_default = datetime.datetime(1990, 8, 31, 23, 46)
        with warnings.catch_warnings(record=True) as catched_warnings:
            DateTimeFieldDefinition.objects.create_with_default(
                model_def=self.model_def,
                name='field_created_with_naive_default',
                default=naive_default
            )
        for warning in catched_warnings:
            if 'received a naive datetime' in warning.message.args[0]:
                break
        else:
            self.fail('No naive datetime warning issued.')


class TimeFieldDefinitionTest(TemporalFieldDefinitionTestMixin,
                              BaseModelDefinitionTestCase):
    field_definition_cls = TimeFieldDefinition
    field_definition_init_kwargs = {'default': datetime.time(1, 1)}
    field_values = (
        datetime.time(1, 58, 37),
        datetime.time(17, 56)
    )
