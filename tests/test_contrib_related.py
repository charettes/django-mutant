from __future__ import unicode_literals

from unittest import skip

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db.models.deletion import ProtectedError
from django.db.models.fields import FieldDoesNotExist
from django.utils.translation import ugettext_lazy as _

from mutant.compat import get_remote_field_model
from mutant.contrib.related.models import (
    ForeignKeyDefinition, ManyToManyFieldDefinition, OneToOneFieldDefinition,
)
from mutant.models import BaseDefinition, ModelDefinition
from mutant.test.testcases import FieldDefinitionTestMixin
from mutant.utils import app_cache_restorer, get_reverse_fields

from .utils import BaseModelDefinitionTestCase


class RelatedFieldDefinitionTestMixin(FieldDefinitionTestMixin):
    field_definition_category = _('Related')

    @classmethod
    def setUpTestData(cls):
        cls.field_definition_init_kwargs = {
            'to': ContentType.objects.get_for_model(ContentType),
            'null': True,
        }
        super(RelatedFieldDefinitionTestMixin, cls).setUpTestData()

    def test_field_clean(self):
        # Refs charettes/django-mutant#5
        try:
            self.field_definition_cls(related_name='related').clean()
        except Exception as e:
            if not isinstance(e, ValidationError):
                self.fail('`clean` method should only raise `ValidationError`')


class ForeignKeyDefinitionTest(RelatedFieldDefinitionTestMixin,
                               BaseModelDefinitionTestCase):
    manual_transaction = True
    field_definition_cls = ForeignKeyDefinition

    def setUp(self):
        self.field_values = (
            ContentType.objects.get_for_model(ContentType),
            ContentType.objects.get_for_model(ModelDefinition),
        )
        super(ForeignKeyDefinitionTest, self).setUp()

    def prepare_default_value(self, value):
        return value.pk

    def test_field_deletion(self):
        def has_reverse_field_on_ct(model_class):
            reverse_fields = get_reverse_fields(ContentType._meta)
            return any(
                reverse_field.related_model == model_class for reverse_field in reverse_fields
            )
        self.assertTrue(has_reverse_field_on_ct(self.model_def.model_class()))
        super(ForeignKeyDefinitionTest, self).test_field_deletion()
        self.assertFalse(has_reverse_field_on_ct(self.model_def.model_class()))

    def test_foreign_key_between_mutable_models(self):
        first_model_def = self.model_def
        second_model_def = ModelDefinition.objects.create(
            app_label='related', object_name='SecondModel'
        )
        FirstModel = first_model_def.model_class()
        SecondModel = second_model_def.model_class()
        second = SecondModel.objects.create()
        ForeignKeyDefinition.objects.create(
            model_def=first_model_def,
            name='second',
            null=True,
            to=second_model_def,
            related_name='first_set'
        )
        self.assertTrue(second.is_obsolete())
        # Make sure dependencies were set correctly
        self.assertSetEqual(
            SecondModel._dependencies,
            set([(ModelDefinition, first_model_def.pk)])
        )
        second = SecondModel.objects.get()
        first = FirstModel.objects.create(second=second)
        # Make sure related managers are correctly assigned
        self.assertEqual(second.first_set.get(), first)
        # Make sure we can filter by a related field
        self.assertEqual(SecondModel.objects.get(first_set=first), second)
        ForeignKeyDefinition.objects.create(
            model_def=second_model_def,
            name='first',
            null=True,
            to=first_model_def,
            related_name='second_set'
        )
        self.assertTrue(first.is_obsolete())
        # Make sure dependencies were set correctly
        self.assertSetEqual(
            FirstModel._dependencies,
            set([(ModelDefinition, second_model_def.pk)])
        )
        self.assertSetEqual(
            SecondModel._dependencies,
            set([(ModelDefinition, first_model_def.pk)])
        )
        second.first = first
        self.assertRaisesMessage(
            ValidationError, 'Cannot save an obsolete model', second.save
        )
        second = SecondModel.objects.get()
        first = FirstModel.objects.get()
        second.first = first
        second.save()
        # Make sure related managers are correctly assigned
        self.assertEqual(first.second_set.get(), second)
        # Make sure we can filter by a related field
        self.assertEqual(FirstModel.objects.get(second_set=second), first)
        second_model_def.delete()

    def test_recursive_relationship(self):
        fk = ForeignKeyDefinition.objects.create(
            model_def=self.model_def, name='f1', null=True, blank=True,
            to=self.model_def
        )
        self.assertTrue(fk.is_recursive_relationship)
        Model = self.model_def.model_class()
        self.assertEqual(get_remote_field_model(Model._meta.get_field('f1')), Model)
        obj1 = Model.objects.create()
        obj2 = Model.objects.create(f1=obj1)
        obj1.f1 = obj2
        obj1.save()

    def test_fixture_loading(self):
        with app_cache_restorer():
            call_command(
                'loaddata', 'test_fk_to_loading.json',
                verbosity=0, commit=False
            )
        to_model_def = ModelDefinition.objects.get_by_natural_key(
            'tests', 'tomodel'
        )
        to_model_class = to_model_def.model_class()
        # Make sure the origin's model class was created
        self.assertTrue(hasattr(to_model_class, 'froms'))
        try:
            from_model_class = to_model_class.froms.field.model
        except AttributeError:
            from_model_class = to_model_class.froms.related.related_model
        try:
            fk_field = from_model_class._meta.get_field('fk')
        except FieldDoesNotExist:
            self.fail('The fk field should be created')
        to_model_class = to_model_def.model_class()
        self.assertEqual(get_remote_field_model(fk_field), to_model_class)
        to_instance = to_model_class.objects.create()
        from_instance = from_model_class.objects.create(fk=to_instance)
        self.assertEqual(to_instance.froms.get(), from_instance)
        to_instance.delete()
        with self.assertRaises(from_model_class.DoesNotExist):
            from_model_class.objects.get(pk=from_instance.pk)


class ForeignKeyDefinitionOnDeleteTest(BaseModelDefinitionTestCase):
    def test_protect(self):
        ForeignKeyDefinition.objects.create(
            model_def=self.model_def, name='f1', null=True,
            to=self.model_def.model_ct,
            on_delete=ForeignKeyDefinition.ON_DELETE_PROTECT
        )
        Model = self.model_def.model_class()
        obj = Model.objects.create()
        Model.objects.create(f1=obj)
        self.assertRaises(ProtectedError, obj.delete)

    def test_set_null(self):
        fk = ForeignKeyDefinition(
            model_def=self.model_def, name='f1', to=self.model_def.model_ct,
            on_delete=ForeignKeyDefinition.ON_DELETE_SET_NULL
        )
        self.assertRaises(ValidationError, fk.clean)
        fk.null = True
        fk.save()
        Model = self.model_def.model_class()
        obj1 = Model.objects.create()
        obj2 = Model.objects.create(f1=obj1)
        obj1.delete()
        self.assertIsNone(Model.objects.get(pk=obj2.pk).f1)

    def test_set_default(self):
        Model = self.model_def.model_class()
        default = Model.objects.create().pk
        fk = ForeignKeyDefinition.objects.create(
            model_def=self.model_def, name='f1', null=True,
            to=self.model_def.model_ct,
            on_delete=ForeignKeyDefinition.ON_DELETE_SET_DEFAULT
        )
        self.assertRaises(ValidationError, fk.clean)
        fk.default = default
        fk.save()
        obj1 = Model.objects.create()
        obj2 = Model.objects.create(f1=obj1)
        obj1.delete()
        self.assertEqual(Model.objects.get(pk=obj2.pk).f1.pk, default)

    def test_set_value(self):
        Model = self.model_def.model_class()
        default = Model.objects.create().pk
        fk = ForeignKeyDefinition.objects.create(
            model_def=self.model_def, name='f1', null=True,
            to=self.model_def.model_ct,
            on_delete=ForeignKeyDefinition.ON_DELETE_SET_VALUE
        )
        self.assertRaises(ValidationError, fk.clean)
        fk.on_delete_set_value = default
        fk.save()
        obj1 = Model.objects.create()
        obj2 = Model.objects.create(f1=obj1)
        obj1.delete()
        self.assertEqual(Model.objects.get(pk=obj2.pk).f1.pk, default)


class OneToOneFieldDefinitionTests(BaseModelDefinitionTestCase):
    def test_parent_link_to_mutable_model(self):
        first_model_def = self.model_def
        second_model_def = ModelDefinition.objects.create(
            app_label='related',
            object_name='SecondModel',
            bases=[BaseDefinition(base=first_model_def.model_class())],
            fields=[
                OneToOneFieldDefinition(
                    name='model',
                    to=first_model_def,
                    related_name='second',
                    parent_link=True,
                ),
            ],
        )
        SecondModel = second_model_def.model_class()
        second_model_instance = SecondModel.objects.create()
        first_model_instance = self.model_def.model_class().objects.get()
        self.assertEqual(second_model_instance.model, first_model_instance)
        self.assertEqual(first_model_instance.second, second_model_instance)


@skip('Incomplete support for many to many field.')
class ManyToManyFieldDefinitionTest(RelatedFieldDefinitionTestMixin,
                                    BaseModelDefinitionTestCase):
    field_definition_cls = ManyToManyFieldDefinition

    def setUp(self):
        self.field_values = (
            [ContentType.objects.get_for_model(ContentType)],
            [ContentType.objects.get_for_model(ModelDefinition),
             ContentType.objects.get_for_model(ContentType)]
        )
        super(ManyToManyFieldDefinitionTest, self).setUp()

    def get_field_value(self, instance, name='field'):
        value = super(RelatedFieldDefinitionTestMixin, self).get_field_value(instance, name)
        return list(value.all())

    def test_field_renaming(self):
        # TODO: investigate why this fails
        return
        value = self.field_values[0]
        Model = self.model_def.model_class()

        instance = Model.objects.create()
        instance.field = value

        self.field.name = 'renamed_field'
        self.field.save()

        instance = Model.objects.get()
        self.assertEqual(instance.renamed_field.all(), value)

        self.assertFalse(hasattr(Model, 'field'))

        instance = Model.objects.create()
        instance.renamed_field = value

    def test_field_default(self):
        # TODO: Investigate why this fails
        pass

    def test_model_save(self):
        # TODO: Investigate why this fails
        pass

    def test_field_unique(self):
        # TODO: Investigate why this fails
        pass

    def test_field_deletion(self):
        # TODO: Investigate why this fails
        pass

    def test_field_symmetrical(self):
        m2m = ManyToManyFieldDefinition(model_def=self.model_def, name='objs')
        ct_ct = ContentType.objects.get_for_model(ContentType)
        m2m.to = ct_ct

        with self.assertRaises(ValidationError):
            m2m.symmetrical = True
            m2m.clean()

        with self.assertRaises(ValidationError):
            m2m.symmetrical = False
            m2m.clean()

        m2m.to = self.model_def.model_ct

        # Make sure `symetrical=True` works
        # m2m.symmetrical = True
        # m2m.clean()
        # m2m.save()

        # Model = self.model_def.model_class()
        # first_object = Model.objects.create()
        # second_object = Model.objects.create()

        # first_object.objs.add(second_object)
        # self.assertIn(first_object, second_object.objs.all())

        # Makes sure non-symmetrical works
        m2m.symmetrical = False
        m2m.clean()
        m2m.save()

        Model = self.model_def.model_class()
        first_object = Model.objects.create()
        second_object = Model.objects.create()

        first_object.objs.add(second_object)
        self.assertNotIn(first_object, second_object.objs.all())

        first_object.objs.clear()
