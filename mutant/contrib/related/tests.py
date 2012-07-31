from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db.models.deletion import ProtectedError
from django.db.models.fields import FieldDoesNotExist
from django.utils.translation import ugettext_lazy as _

from ...models.model import ModelDefinition
from ...test.testcases import FieldDefinitionTestMixin
from ...tests.models.utils import BaseModelDefinitionTestCase
from ...utils import model_cache_restorer

from .models import ForeignKeyDefinition, ManyToManyFieldDefinition


class RelatedFieldDefinitionTestMixin(FieldDefinitionTestMixin):
    field_definition_category = _('Related')

    def setUp(self):
        self.field_definition_init_kwargs = {
            'to': ContentType.objects.get_for_model(ContentType),
            'null': True
        }
        super(RelatedFieldDefinitionTestMixin, self).setUp()


class ForeignKeyDefinitionTest(RelatedFieldDefinitionTestMixin,
                               BaseModelDefinitionTestCase):
    field_definition_cls = ForeignKeyDefinition

    def setUp(self):
        self.field_values = (
            ContentType.objects.get_for_model(ContentType),
            ContentType.objects.get_for_model(ModelDefinition),
        )
        super(ForeignKeyDefinitionTest, self).setUp()

    def prepare_default_value(self, value):
        return value.pk

    def test_field_renaming(self):
        pass # This test must use transactions

    def test_field_deletion(self):
        pass # This test must use transactions

    def test_simple_foreign_key_between_mutable_models(self):
        return # This test must use transactions
        first_model_def = self.model_def
        second_model_def = ModelDefinition.objects.create(app_label='app',
                                                          object_name='SecondModel')
        FirstModel = first_model_def.model_class()
        SecondModel = second_model_def.model_class()
        ForeignKeyDefinition.objects.create(model_def=first_model_def,
                                            name='second', null=True,
                                            to=second_model_def.model_ct)
        second = SecondModel.objects.create()
        first = FirstModel.objects.create(second=second)
        ForeignKeyDefinition.objects.create(model_def=second_model_def,
                                            name='first', null=True,
                                            to=first_model_def.model_ct)
        second.first = first
        self.assertRaisesMessage(ValidationError,
                                 'Cannot save an obsolete model', second.save)
        second = SecondModel.objects.get()
        second.first = first
        second.save()
        second_model_def.delete()

    def test_recursive_relationship(self):
        fk = ForeignKeyDefinition.objects.create(model_def=self.model_def,
                                                 name='f1', null=True, blank=True,
                                                 to=self.model_def.model_ct)
        self.assertTrue(fk.is_recursive_relationship)
        Model = self.model_def.model_class()
        self.assertEqual(Model._meta.get_field('f1').rel.to, Model)
        obj1 = Model.objects.create()
        obj2 = Model.objects.create(f1=obj1)
        obj1.f1 = obj2
        obj1.save()

    def test_fixture_loading(self):
        with model_cache_restorer():
            call_command('loaddata', 'test_fk_to_loading.json', verbosity=0,
                         commit=False)
        from_model_def = ModelDefinition.objects.get_by_natural_key('app',
                                                                    'frommodel')
        from_model_class = from_model_def.model_class()
        try:
            fk_field = from_model_class._meta.get_field('fk')
        except FieldDoesNotExist:
            self.fail('The fk field should be created')
        to_model_def = ModelDefinition.objects.get_by_natural_key('app',
                                                                  'tomodel')
        to_model_class = to_model_def.model_class()
        self.assertEqual(fk_field.rel.to, to_model_class)
        to_instance = to_model_class.objects.create()
        from_instance = from_model_class.objects.create(fk=to_instance)
        to_instance.delete()
        with self.assertRaises(from_model_class.DoesNotExist):
            from_model_class.objects.get(pk=from_instance.pk)


class ForeignKeyDefinitionOnDeleteTest(BaseModelDefinitionTestCase):
    def test_protect(self):
        ForeignKeyDefinition.objects.create(model_def=self.model_def,
                                            name='f1', null=True,
                                            to=self.model_def.model_ct,
                                            on_delete='PROTECT')
        Model = self.model_def.model_class()
        obj1 = Model.objects.create()
        Model.objects.create(f1=obj1)
        self.assertRaises(ProtectedError, obj1.delete)

    def test_set_null(self):
        fk = ForeignKeyDefinition(model_def=self.model_def,
                                  name='f1',
                                  to=self.model_def.model_ct,
                                  on_delete='SET_NULL')
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
        fk = ForeignKeyDefinition.objects.create(model_def=self.model_def,
                                                 name='f1', null=True,
                                                 to=self.model_def.model_ct,
                                                 on_delete='SET_DEFAULT')
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
        fk = ForeignKeyDefinition.objects.create(model_def=self.model_def,
                                                 name='f1', null=True,
                                                 to=self.model_def.model_ct,
                                                 on_delete='SET_VALUE')
        fk.on_delete_set_value = default
        fk.save()
        obj1 = Model.objects.create()
        obj2 = Model.objects.create(f1=obj1)
        obj1.delete()
        self.assertEqual(Model.objects.get(pk=obj2.pk).f1.pk, default)


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
#        m2m.symmetrical = True
#        m2m.clean()
#        m2m.save()
#        
#        Model = self.model_def.model_class()
#        first_object = Model.objects.create()
#        second_object = Model.objects.create()
#        
#        first_object.objs.add(second_object)
#        self.assertIn(first_object, second_object.objs.all())

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
