from __future__ import unicode_literals

import pickle
from unittest.case import expectedFailure

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import connection, connections, models, router, transaction
from django.db.utils import IntegrityError
from django.test.utils import CaptureQueriesContext
from django.utils.translation import ugettext as _

from mutant.compat import many_to_many_set
from mutant.contrib.related.models import ForeignKeyDefinition
from mutant.contrib.text.models import CharFieldDefinition
from mutant.db.models import MutableModel
from mutant.models.model import (
    BaseDefinition, ModelDefinition, MutableModelProxy,
    OrderingFieldDefinition, UniqueTogetherDefinition,
)
from mutant.utils import clear_opts_related_cache, remove_from_app_cache

from .models import (
    AbstractConcreteModelSubclass, AbstractModel, Mixin,
    ModelSubclassWithTextField, ProxyModel,
)
from .utils import BaseModelDefinitionTestCase

# Remove when dropping support for Python 2
try:
    from test.support import captured_stderr
except ImportError:
    from test.test_support import captured_stderr


class ModelDefinitionTest(BaseModelDefinitionTestCase):
    def test_model_class_creation_cache(self):
        existing_model_class = self.model_def.model_class().model
        self.assertIs(
            self.model_def.model_class().model, existing_model_class
        )
        self.assertIsNot(
            self.model_def.model_class(force_create=True).model, existing_model_class
        )

    def test_force_create_checksum(self):
        """Recreating a model with no changes shouldn't change it's checksum"""
        with self.assertChecksumDoesntChange():
            self.model_def.model_class(force_create=True)

    def test_repr(self):
        """Make sure ModelDefinition objects are always repr()-able."""
        repr(self.model_def)
        repr(ModelDefinition())

    def get_model_db_table_name(self, model_def):
        model_class = model_def.model_class()
        return router.db_for_write(model_class), model_class._meta.db_table

    def test_app_label_rename(self):
        db, table_name = self.get_model_db_table_name(self.model_def)

        with self.assertChecksumChange(self.model_def):
            self.model_def.app_label = 'contenttypes'
            self.model_def.save(update_fields=['app_label'])

        self.assertEqual(
            self.model_def.model_class().__module__,
            'django.contrib.contenttypes.models'
        )

        self.assertTableDoesntExists(db, table_name)
        db, table_name = self.get_model_db_table_name(self.model_def)
        self.assertTableExists(db, table_name)

    def test_object_name_rename(self):
        db, table_name = self.get_model_db_table_name(self.model_def)

        with self.assertChecksumChange(self.model_def):
            self.model_def.object_name = 'MyModel'
            self.model_def.save(update_fields=['object_name', 'model'])

        self.assertTableDoesntExists(db, table_name)
        db, table_name = self.get_model_db_table_name(self.model_def)
        self.assertTableExists(db, table_name)

    def test_db_table_change(self):
        """Asserts that the `db_table` field is correctly handled."""
        db, table_name = self.get_model_db_table_name(self.model_def)

        with self.assertChecksumChange():
            self.model_def.db_table = 'test_db_table'
            self.model_def.save(update_fields=['db_table'])

        self.assertTableDoesntExists(db, table_name)
        self.assertTableExists(db, 'test_db_table')

        with self.assertChecksumChange():
            self.model_def.db_table = None
            self.model_def.save(update_fields=['db_table'])

        self.assertTableDoesntExists(db, 'test_db_table')
        self.assertTableExists(db, table_name)

    def test_fixture_loading(self):
        """Make model and field definitions can be loaded from fixtures."""
        call_command(
            'loaddata', 'fixture_loading_test', verbosity=0, commit=False
        )
        self.assertTrue(
            ModelDefinition.objects.filter(
                app_label='tests', object_name='MyFixtureModel'
            ).exists()
        )
        model_def = ModelDefinition.objects.get(
            app_label='tests', object_name='MyFixtureModel'
        )
        MyFixtureModel = model_def.model_class()
        self.assertModelTablesExist(MyFixtureModel)
        # Makes sure concrete field definition subclasses are created...
        self.assertTrue(
            model_def.fielddefinitions.filter(
                name='fixture_charfield'
            ).exists()
        )
        # and their column is created.
        self.assertModelTablesColumnExists(MyFixtureModel, 'fixture_charfieldcolumn')
        # Makes sure proxy field definition subclasses are created...
        self.assertTrue(
            model_def.fielddefinitions.filter(
                name='fixture_integerfield'
            ).exists()
        )
        # and their column is created.
        self.assertModelTablesColumnExists(MyFixtureModel, 'fixture_integerfieldcolumn')

    def test_verbose_name(self):
        model_class = self.model_def.model_class()

        self.assertEqual(model_class._meta.verbose_name, 'model')

        with self.assertChecksumChange():
            self.model_def.verbose_name = 'MyModel'
            self.model_def.save(update_fields=['verbose_name'])

        self.assertEqual(
            model_class._meta.verbose_name, self.model_def.verbose_name
        )

    def test_verbose_name_plural(self):
        model_class = self.model_def.model_class()

        self.assertEqual(model_class._meta.verbose_name_plural, 'models')

        with self.assertChecksumChange():
            self.model_def.verbose_name_plural = 'MyModels'
            self.model_def.save(update_fields=['verbose_name_plural'])

        self.assertEqual(
            model_class._meta.verbose_name_plural,
            self.model_def.verbose_name_plural
        )

    def test_multiple_model_definition(self):
        """Make sure multiple model definition can coexist."""
        other_model_def = ModelDefinition.objects.create(
            app_label='mutant', object_name='OtherModel'
        )
        self.assertNotEqual(
            other_model_def.model_class(), self.model_def.model_class()
        )
        self.assertNotEqual(other_model_def.model_ct, self.model_def.model_ct)

    def test_natural_key(self):
        natural_key = self.model_def.natural_key()
        self.assertEqual(
            ModelDefinition.objects.get_by_natural_key(*natural_key),
            self.model_def
        )

    def test_deletion(self):
        # Add a an extra field to make sure no alter statements are issued
        with self.assertChecksumChange():
            CharFieldDefinition.objects.create(
                model_def=self.model_def,
                name='field',
                max_length=10
            )
        # Add a base with a field to make sure no alter statements are issued
        with self.assertChecksumChange():
            BaseDefinition.objects.create(
                model_def=self.model_def,
                base=AbstractModel
            )
        model_cls = self.model_def.model_class()
        self.assertModelTablesExist(model_cls)
        db, table_name = self.get_model_db_table_name(self.model_def)
        connection = connections[db]
        with CaptureQueriesContext(connection) as captured_queries:
            self.model_def.delete()
        # Ensure no ALTER queries were issued during deletion of model_def,
        # that is, check that the columns were not deleted on table one at a
        # time before the entire table was dropped.
        self.assertFalse(
            any('ALTER' in query['sql'] for query in captured_queries)
        )
        self.assertTableDoesntExists(db, table_name)

    def test_model_management(self):
        """Make sure no DDL is executed when a model is marked as managed."""
        model_def = self.model_def
        CharFieldDefinition.objects.create(
            model_def=model_def,
            name='field',
            max_length=10
        )
        model_cls = model_def.model_class()
        model_cls.objects.create(field='test')
        # Mark the existing model definition as `managed`.
        model_def.managed = True
        model_def.save()
        # Deleting a managed model shouldn't issue a DROP TABLE.
        db, table_name = self.get_model_db_table_name(self.model_def)
        model_def.delete()
        self.assertTableExists(db, table_name)
        # Attach a new model definition to the existing table
        new_model_def = ModelDefinition.objects.create(
            app_label=model_def.app_label,
            object_name=model_def.object_name,
            managed=True,
            fields=(CharFieldDefinition(name='field', max_length=10),)
        )
        # Make sure old data can be retrieved
        self.assertEqual(1, new_model_def.model_class().objects.count())
        # Mark the new model as unmanaged to make sure it's associated
        # table is deleted on tear down.
        new_model_def.managed = False
        new_model_def.save()


class ModelDefinitionManagerTest(BaseModelDefinitionTestCase):
    def test_fields_creation(self):
        char_field = CharFieldDefinition(name='name', max_length=10)
        ct_ct = ContentType.objects.get_for_model(ContentType)
        fk_field = ForeignKeyDefinition(name='ct', to=ct_ct)
        model_def = ModelDefinition.objects.create(
            app_label='mutant', object_name='OtherModel',
            fields=[char_field, fk_field]
        )
        model_cls = model_def.model_class()
        db = router.db_for_write(model_cls)
        table = model_cls._meta.db_table
        column = model_cls._meta.get_field('name').get_attname_column()[1]
        # Make sure column was created
        self.assertColumnExists(db, table, column)
        # Make sure field definitions were created
        self.assertIsNotNone(char_field.pk)
        self.assertIsNotNone(fk_field.pk)

    def test_bases_creation(self):
        mixin_base = BaseDefinition(base=Mixin)
        abstract_base = BaseDefinition(base=AbstractModel)
        abstract_concrete_base = BaseDefinition(
            base=AbstractConcreteModelSubclass
        )
        model_def = ModelDefinition.objects.create(
            app_label='mutant', object_name='OtherModel',
            bases=[mixin_base, abstract_base, abstract_concrete_base],
        )
        model = model_def.model_class()
        self.assertModelTablesColumnDoesntExists(model, 'id')
        self.assertModelTablesColumnExists(model, 'concretemodel_ptr_id')
        self.assertModelTablesColumnExists(model, 'abstract_model_field')
        self.assertModelTablesColumnDoesntExists(model, 'concrete_model_field')
        self.assertModelTablesColumnExists(
            model, 'abstract_concrete_model_subclass_field'
        )

    def test_primary_key_override(self):
        field = CharFieldDefinition(
            name='name', max_length=32, primary_key=True
        )
        model_def = ModelDefinition.objects.create(
            fields=[field], app_label='mutant', object_name='OtherModel'
        )
        self.assertEqual(model_def.model_class()._meta.pk.name, field.name)

    def test_get_or_create(self):
        """
        Make sure bases and fields defaults are reaching the model initializer.
        """
        field = CharFieldDefinition(name='name', max_length=32)
        base = BaseDefinition(base=AbstractModel)
        ModelDefinition.objects.get_or_create(
            app_label='mutant', object_name='OtherModel',
            defaults={'bases': [base], 'fields': [field]}
        )
        self.assertIsNotNone(field.pk)
        self.assertIsNotNone(base.pk)


class MutableModelProxyTest(BaseModelDefinitionTestCase):
    def test_pickling(self):
        """Make sure `MutableModelProxy` instances can be pickled correctly.
        This is required for mutable model inheritance."""
        proxy = self.model_def.model_class()
        pickled = pickle.dumps(proxy)
        self.assertEqual(pickle.loads(pickled), proxy)
        self.assertEqual(pickle.loads(pickled), proxy.model)

    def test_type_checks(self):
        proxy = self.model_def.model_class()
        self.assertTrue(issubclass(proxy, models.Model))
        self.assertTrue(issubclass(proxy, MutableModel))
        self.assertFalse(issubclass(proxy, MutableModelProxyTest))
        self.assertIsInstance(proxy, models.base.ModelBase)
        self.assertIsInstance(proxy, MutableModelProxy)
        self.assertFalse(isinstance(proxy, MutableModelProxyTest))

    def test_instance_checks(self):
        proxy = self.model_def.model_class()
        instance = proxy()
        self.assertIsInstance(instance, proxy)
        self.assertIsInstance(instance, proxy.model)

    def test_contains(self):
        proxy = self.model_def.model_class()
        self.assertIn(proxy, set([proxy.model]))
        self.assertIn(proxy.model, set([proxy]))

    def test_equality(self):
        p1 = self.model_def.model_class()
        p2 = self.model_def.model_class()
        self.assertEqual(p1, p2)  # Test underlying model retrieval
        self.assertEqual(p1, p2.model)  # Test direct model comparison
        self.assertNotEqual(p1, 'string')  # Test type comparison
        # Test underlying model class comparison
        m1 = p1.model
        p3 = self.model_def.model_class(force_create=True)
        self.assertNotEqual(p3, m1)

    def test_proxy_interactions(self):
        CharFieldDefinition.objects.create(
            model_def=self.model_def, name="name", max_length=10
        )
        proxy = self.model_def.model_class()
        # Attribute access
        sergei = proxy.objects.create(name='Sergei')
        # Callable access
        halak = proxy(name='Halak')
        halak.save()
        self.assertEqual(
            "<class 'mutant.models.Model'>", str(proxy)
        )
        self.assertEqual(sergei, proxy.objects.get(name='Sergei'))

        class A(object):
            class_model = proxy

            def __init__(self, model):
                self.model = model

        a = A(proxy)

        self.assertEqual(proxy, a.model)
        self.assertEqual(proxy, A.class_model)

        a.model = proxy  # Assign a proxy
        a.model = a.model  # Assign a Model
        a.model = 4

    def test_definition_deletion(self):
        CharFieldDefinition.objects.create(model_def=self.model_def,
                                           name="name", max_length=10)

        Model = self.model_def.model_class()
        db = router.db_for_write(Model)
        instance = Model.objects.create(name="Quebec")
        table_name = Model._meta.db_table
        self.model_def.delete()
        self.assertTableDoesntExists(db, table_name)

        with self.assertRaisesMessage(
            AttributeError,
            'The definition of mutant.Model has been deleted.'
        ):
            Model(name="name")

        with self.assertRaisesMessage(
            AttributeError,
            'The definition of mutant.Model has been deleted.'
        ):
            Model.objects.all()

        with self.assertRaises(ValidationError):
            instance.clean()

        with self.assertRaises(ValidationError):
            instance.save()

        with self.assertRaises(ValidationError):
            instance.delete()

    def test_refreshing_safeguard(self):
        """Make sure model refreshing that occurs when a model class is
        obsolete doesn't hang when a model class in the app_cache points to
        the obsolete one thus triggering a chain of refreshing indirectly
        caused by related objects cache."""
        proxy = self.model_def.model_class()
        model = proxy.model
        # Create a FK pointing to a  model class that will become obsolete
        fk = models.ForeignKey(to=proxy, on_delete=models.CASCADE)
        fk.contribute_to_class(model, 'fk')
        model.mark_as_obsolete()
        # Clear up the related cache of ModelDefiniton to make sure
        # _fill_related_objects_cache` is called.
        clear_opts_related_cache(ModelDefinition)
        self.assertTrue(model.is_obsolete())
        # Trigger model refreshing to make sure the `refreshing` safe guard works
        self.assertFalse(proxy.is_obsolete())
        # Cleanup the FK to avoid test pollution.
        model._meta.local_fields.remove(fk)


class OrderingDefinitionTest(BaseModelDefinitionTestCase):
    @classmethod
    def setUpTestData(cls):
        super(OrderingDefinitionTest, cls).setUpTestData()
        with cls.assertChecksumChange():
            cls.f1_pk = CharFieldDefinition.objects.create(
                model_def_id=cls.model_def_pk, name='f1', max_length=25
            ).pk
        ct_ct = ContentType.objects.get_for_model(ContentType)
        with cls.assertChecksumChange():
            cls.f2_pk = ForeignKeyDefinition.objects.create(
                model_def_id=cls.model_def_pk, null=True, name='f2', to=ct_ct
            ).pk

    def setUp(self):
        super(OrderingDefinitionTest, self).setUp()
        self.f1 = CharFieldDefinition.objects.get(pk=self.f1_pk)
        self.f2 = ForeignKeyDefinition.objects.get(pk=self.f2_pk)

    def test_clean(self):
        ordering = OrderingFieldDefinition(model_def=self.model_def)
        # Random
        ordering.lookup = '?'
        ordering.clean()
        # By f1
        ordering.lookup = 'f1'
        ordering.clean()
        # By f2 app label
        ordering.lookup = 'f2__app_label'
        ordering.clean()
        # Inexistent field
        with self.assertRaises(ValidationError):
            ordering.lookup = 'inexistent_field'
            ordering.clean()
        # Inexistent field of an existent field
        with self.assertRaises(ValidationError):
            ordering.lookup = 'f2__higgs_boson'
            ordering.clean()

    def test_simple_ordering(self):
        Model = self.model_def.model_class()
        model_ct = ContentType.objects.get_for_model(Model)  # app
        ct_ct = ContentType.objects.get_for_model(ContentType)  # contenttypes
        Model.objects.create(f1='Simon', f2=ct_ct)
        Model.objects.create(f1='Alexander', f2=model_ct)
        # Instances should be sorted by id
        self.assertSequenceEqual(
            Model.objects.values_list('f1', flat=True), ('Simon', 'Alexander')
        )
        # Instances should be sorted by f1 and not id
        with self.assertChecksumChange():
            f1_ordering = OrderingFieldDefinition.objects.create(
                model_def=self.model_def, lookup='f1'
            )
        self.assertSequenceEqual(
            Model.objects.values_list('f1', flat=True), ('Alexander', 'Simon')
        )
        # Swap the ordering to descending
        with self.assertChecksumChange():
            f1_ordering.descending = True
            f1_ordering.save()
        self.assertSequenceEqual(
            Model.objects.values_list('f1', flat=True), ('Simon', 'Alexander')
        )
        with self.assertChecksumChange():
            f1_ordering.delete()
        # Order by f2__app_label
        with self.assertChecksumChange():
            f2_ordering = OrderingFieldDefinition.objects.create(
                model_def=self.model_def, lookup='f2__app_label'
            )
        self.assertSequenceEqual(
            Model.objects.values_list('f1', flat=True), ('Simon', 'Alexander')
        )
        # Swap the ordering to descending
        with self.assertChecksumChange():
            f2_ordering.descending = True
            f2_ordering.save()
        self.assertSequenceEqual(
            Model.objects.values_list('f1', flat=True), ('Alexander', 'Simon')
        )
        with self.assertChecksumChange():
            f2_ordering.delete()

    def test_multiple_ordering(self):
        Model = self.model_def.model_class()
        model_ct = ContentType.objects.get_for_model(Model)  # app
        ct_ct = ContentType.objects.get_for_model(ContentType)  # contenttypes
        Model.objects.create(f1='Simon', f2=ct_ct)
        Model.objects.create(f1='Alexander', f2=model_ct)
        Model.objects.create(f1='Julia', f2=ct_ct)
        Model.objects.create(f1='Alexander', f2=ct_ct)
        # Orderings
        with self.assertChecksumChange():
            f1_ordering = OrderingFieldDefinition.objects.create(
                model_def=self.model_def, lookup='f1'
            )
        with self.assertChecksumChange():
            f2_ordering = OrderingFieldDefinition.objects.create(
                model_def=self.model_def, lookup='f2__app_label'
            )
        self.assertSequenceEqual(
            Model.objects.values_list('f1', 'f2__app_label'), (
                ('Alexander', 'contenttypes'),
                ('Alexander', 'mutant'),
                ('Julia', 'contenttypes'),
                ('Simon', 'contenttypes'),
            )
        )
        # Swap the ordering to descending
        with self.assertChecksumChange():
            f2_ordering.descending = True
            f2_ordering.save()
        self.assertSequenceEqual(
            Model.objects.values_list('f1', 'f2__app_label'), (
                ('Alexander', 'mutant'),
                ('Alexander', 'contenttypes'),
                ('Julia', 'contenttypes'),
                ('Simon', 'contenttypes'),
            )
        )
        # Swap order
        f1_ordering.order, f2_ordering.order = f2_ordering.order, f1_ordering.order
        with self.assertChecksumChange():
            f1_ordering.save()
            f2_ordering.save()
        self.assertSequenceEqual(
            Model.objects.values_list('f1', 'f2__app_label'), (
                ('Alexander', 'mutant'),
                ('Alexander', 'contenttypes'),
                ('Julia', 'contenttypes'),
                ('Simon', 'contenttypes'),
            )
        )
        # Swap the ordering to descending
        with self.assertChecksumChange():
            f1_ordering.descending = True
            f1_ordering.save()
        self.assertSequenceEqual(
            Model.objects.values_list('f1', 'f2__app_label'), (
                ('Alexander', 'mutant'),
                ('Simon', 'contenttypes'),
                ('Julia', 'contenttypes'),
                ('Alexander', 'contenttypes'),
            )
        )
        with self.assertChecksumChange():
            f1_ordering.delete()
        with self.assertChecksumChange():
            f2_ordering.delete()


class UniqueTogetherDefinitionTest(BaseModelDefinitionTestCase):
    @classmethod
    def setUpTestData(cls):
        super(UniqueTogetherDefinitionTest, cls).setUpTestData()
        with cls.assertChecksumChange():
            cls.f1_pk = CharFieldDefinition.objects.create(
                model_def_id=cls.model_def_pk, name='f1', max_length=25
            ).pk
        with cls.assertChecksumChange():
            cls.f2_pk = CharFieldDefinition.objects.create(
                model_def_id=cls.model_def_pk, name='f2', max_length=25
            ).pk
        cls.ut_pk = UniqueTogetherDefinition.objects.create(
            model_def_id=cls.model_def_pk
        ).pk

    def setUp(self):
        super(UniqueTogetherDefinitionTest, self).setUp()
        self.f1 = CharFieldDefinition.objects.get(pk=self.f1_pk)
        self.f2 = CharFieldDefinition.objects.get(pk=self.f2_pk)
        self.ut = UniqueTogetherDefinition.objects.get(pk=self.ut_pk)
        self.model_class = self.model_def.model_class()

    def test_repr(self):
        """Make sure UniqueTogetherDefinition objects are always
        repr()-able."""
        repr(self.ut)
        repr(UniqueTogetherDefinition())

    def test_clean(self):
        """Make sure we can't create a unique key with two fields of two
        different models"""
        other_model_def = ModelDefinition.objects.create(
            app_label='mutant', object_name='OtherModel'
        )
        with self.assertChecksumChange(other_model_def):
            f2 = CharFieldDefinition.objects.create(
                model_def=other_model_def, name='f2', max_length=25
            )
        many_to_many_set(self.ut, 'field_defs', [self.f1, f2])
        self.assertRaises(ValidationError, self.ut.clean)

    def test_db_column(self):
        """Make sure a unique index creation works correctly when using a
        custom `db_column`. This is needed for unique FK's columns."""
        self.f2.db_column = 'f2_column'
        self.f2.save()
        many_to_many_set(self.ut, 'field_defs', [self.f1, self.f2])
        self.f2.db_column = 'f2'
        self.f2.save()
        self.ut.delete()

    def test_cannot_create_unique(self):
        """Creating a unique key on a table with duplicate rows
        shouldn't work"""
        self.model_class.objects.create(f1='a', f2='b')
        self.model_class.objects.create(f1='a', f2='b')
        with captured_stderr():
            with self.assertRaises(IntegrityError):
                with transaction.atomic():
                    many_to_many_set(self.ut, 'field_defs', [self.f1, self.f2])
    if connection.settings_dict['ENGINE'] == 'django.db.backends.sqlite3':
        # TODO: Figure out why this is failing for Django 1.9 + against SQLite
        # on TravisCI.
        test_cannot_create_unique = expectedFailure(test_cannot_create_unique)

    def test_cannot_insert_duplicate_row(self):
        """Inserting a duplicate rows shouldn't work."""
        self.model_class.objects.create(f1='a', f2='b')
        many_to_many_set(self.ut, 'field_defs', [self.f1, self.f2])
        with captured_stderr():
            with self.assertRaises(IntegrityError):
                with transaction.atomic():
                    self.model_class.objects.create(f1='a', f2='b')

    def test_cannot_remove_unique(self):
        """Removing a unique constraint that cause duplicate rows shouldn't
        work."""
        many_to_many_set(self.ut, 'field_defs', [self.f1, self.f2])
        self.model_class.objects.create(f1='a', f2='b')
        self.model_class.objects.create(f1='a', f2='c')
        with captured_stderr():
            with self.assertRaises(IntegrityError):
                with transaction.atomic():
                    self.ut.field_defs.remove(self.f2)
    if connection.settings_dict['ENGINE'] == 'django.db.backends.sqlite3':
        # TODO: Figure out why this is failing for Django 1.9 + against SQLite
        # on TravisCI.
        test_cannot_remove_unique = expectedFailure(test_cannot_remove_unique)

    def test_clear_removes_unique(self):
        """
        Removing a unique constraint should relax duplicate row
        validation
        """
        self.model_class.objects.create(f1='a', f2='b')
        many_to_many_set(self.ut, 'field_defs', [self.f1, self.f2])
        self.ut.field_defs.clear()
        self.model_class.objects.create(f1='a', f2='b')


class BaseDefinitionTest(BaseModelDefinitionTestCase):
    def test_clean(self):
        bd = BaseDefinition(model_def=self.model_def)
        # Base must be a class
        bd.base = BaseDefinitionTest.test_clean
        self.assertRaisesMessage(
            ValidationError, _('Base must be a class.'), bd.clean
        )
        # Subclasses of MutableModel are valid bases
        bd.base = ModelDefinition.objects.create(
            app_label='mutant', object_name='AnotherModel'
        ).model_class()
        try:
            bd.clean()
        except ValidationError:
            self.fail('MutableModel subclasses are valid bases.')
        # But model definition can't be bases of themselves
        bd.base = self.model_def.model_class()
        self.assertRaisesMessage(
            ValidationError,
            _("A model definition can't be a base of itself."),
            bd.clean
        )
        # Mixin objets are valid bases
        bd.base = Mixin
        try:
            bd.clean()
        except ValidationError:
            self.fail('Mixin objets are valid bases.')
        # Abstract model subclasses are valid bases
        bd.base = AbstractModel
        try:
            bd.clean()
        except ValidationError:
            self.fail('Abstract Model are valid bases')
        # Proxy model are not valid bases
        bd.base = ProxyModel
        self.assertRaisesMessage(
            ValidationError, _("Base can't be a proxy model."), bd.clean
        )

    def test_mutable_model_base(self):
        another_model_def = ModelDefinition.objects.create(
            app_label='mutant', object_name='AnotherModel'
        )
        another_model_class = another_model_def.model_class()
        auto_pk_column = another_model_class._meta.pk.get_attname_column()[1]
        self.assertModelTablesColumnExists(another_model_class, auto_pk_column)
        with self.assertChecksumChange():
            CharFieldDefinition.objects.create(
                model_def=self.model_def, name='f1', max_length=25
            )
        model_class = self.model_def.model_class()
        with self.assertChecksumChange(another_model_def):
            base_definition = BaseDefinition(model_def=another_model_def)
            base_definition.base = model_class
            base_definition.save()
        self.assertModelTablesColumnDoesntExists(another_model_class, auto_pk_column)
        self.assertEqual(model_class.anothermodel.related.related_model, another_model_class)
        remove_from_app_cache(another_model_class).mark_as_obsolete()
        self.assertFalse(hasattr(model_class, 'anothermodel'))
        another_model = another_model_class.objects.create(f1='Martinal')
        self.assertTrue(hasattr(model_class, 'anothermodel'))
        self.assertTrue(another_model_class.objects.exists())
        with self.assertChecksumChange():
            with self.assertChecksumChange(another_model_def):
                CharFieldDefinition.objects.create(
                    model_def=self.model_def, name='f2', max_length=25,
                    null=True
                )
        another_model = another_model_class.objects.get(pk=another_model.pk)
        self.assertIsNone(another_model.f2)
        another_model.f2 = 'Placebo'
        another_model.save()

    def test_base_inheritance(self):
        model_class = self.model_def.model_class()
        with self.assertChecksumChange():
            BaseDefinition.objects.create(
                model_def=self.model_def, base=Mixin
            )
        self.assertTrue(issubclass(model_class, Mixin))
        with self.assertChecksumChange():
            BaseDefinition.objects.create(
                model_def=self.model_def, base=AbstractModel
            )
        self.assertTrue(
            issubclass(model_class, Mixin) and
            issubclass(model_class, AbstractModel)
        )

    def test_base_ordering(self):
        model_class = self.model_def.model_class()
        with self.assertChecksumChange():
            mixin_base_def = BaseDefinition.objects.create(
                model_def=self.model_def, base=Mixin
            )
        with self.assertChecksumChange():
            abstract_base_def = BaseDefinition.objects.create(
                model_def=self.model_def, base=AbstractModel
            )
        instance = model_class()
        self.assertEqual('Mixin', instance.method())
        with self.assertChecksumChange():
            mixin_base_def.order = abstract_base_def.order + 1
            mixin_base_def.save(update_fields=['order'])
        instance = model_class()
        self.assertEqual('AbstractModel', instance.method())
        with self.assertChecksumChange():
            abstract_base_def.order = mixin_base_def.order + 1
            abstract_base_def.save(update_fields=['order'])
        instance = model_class()
        self.assertEqual('Mixin', instance.method())

    def test_abstract_field_inherited(self):
        with self.assertChecksumChange():
            bd = BaseDefinition.objects.create(
                model_def=self.model_def, base=AbstractModel
            )
        model_class = self.model_def.model_class()
        model_class.objects.create(abstract_model_field='value')
        # Test column alteration and addition by replacing the base with
        # a new one with a field with the same name and a second field.
        with self.assertChecksumChange():
            bd.base = ModelSubclassWithTextField
            bd.save()
        model_class.objects.get(abstract_model_field='value')
        # The original CharField should be replaced by a TextField with no
        # max_length and a second field should be added
        model_class.objects.create(
            abstract_model_field='another one bites the dust',
            second_field=True
        )
        # Test column deletion by deleting the base
        # This should cause the model to loose all it's fields and the table
        # to loose all it's columns
        with self.assertChecksumChange():
            bd.delete()
        self.assertEqual(
            list(model_class.objects.values_list()), list(
                model_class.objects.values_list('pk')
            )
        )
        self.assertModelTablesColumnDoesntExists(model_class, 'field')
