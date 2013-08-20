from __future__ import unicode_literals

import pickle

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import connections, models, router
from django.db.utils import IntegrityError
from django.utils.translation import ugettext_lazy as _

from mutant.contrib.text.models import CharFieldDefinition
from mutant.contrib.related.models import ForeignKeyDefinition
from mutant.db.models import MutableModel
from mutant.models.model import (ModelDefinition, OrderingFieldDefinition,
    UniqueTogetherDefinition, BaseDefinition)
from mutant.test.utils import CaptureQueriesContext

from .utils import (BaseModelDefinitionTestCase,
    skipUnlessMutantModelDBFeature)


try:
    from test.test_support import captured_stderr
except ImportError:
    # python 2.6 doesn't provide this helper
    from contextlib import contextmanager
    import StringIO
    import sys

    @contextmanager
    def captured_stderr():
        stderr = sys.stderr
        try:
            sys.stderr = StringIO.StringIO()
            yield sys.stderr
        finally:
            sys.stderr = stderr


class Mixin(object):
    def method(self):
        return 'Mixin'


class ConcreteModel(models.Model):
    concrete_model_field = models.NullBooleanField()

    class Meta:
        app_label = 'mutant'


class ProxyModel(ConcreteModel):
    class Meta:
        proxy = True


class AbstractModel(models.Model):
    abstract_model_field = models.CharField(max_length=5)

    class Meta:
        abstract = True

    def method(self):
        return 'AbstractModel'


class AbstractConcreteModelSubclass(ConcreteModel):
    abstract_concrete_model_subclass_field = models.CharField(max_length=5)

    class Meta:
        abstract = True


class ModelSubclassWithTextField(models.Model):
    abstract_model_field = models.TextField()
    second_field = models.NullBooleanField()

    class Meta:
        abstract = True


class ModelDefinitionTest(BaseModelDefinitionTestCase):
    def test_model_class_creation_cache(self):
        Model = self.model_def.model_class()
        self.assertEqual(Model, self.model_def.model_class())
        self.assertNotEqual(Model, self.model_def.model_class(force_create=True))

    def test_repr(self):
        """
        Make sure ModelDefinition objects are always repr()-able.
        """
        repr(self.model_def)
        repr(ModelDefinition())

    def get_model_db_table_name(self, model_def):
        model_class = model_def.model_class()
        return router.db_for_write(model_class), model_class._meta.db_table

    def test_rename_model(self):
        """
        Make sure changing the app_label or object_name renames the associated
        table
        """
        db, table_name = self.get_model_db_table_name(self.model_def)
        self.model_def.app_label = 'myapp'
        self.model_def.save()
        self.assertTableDoesntExists(db, table_name)
        db, table_name = self.get_model_db_table_name(self.model_def)
        self.assertTableExists(db, table_name)

        self.model_def.object_name = 'MyModel'
        self.model_def.save()
        self.assertTableDoesntExists(db, table_name)
        db, table_name = self.get_model_db_table_name(self.model_def)
        self.assertTableExists(db, table_name)

        self.model_def.delete()
        self.assertTableDoesntExists(db, table_name)

    def test_db_table(self):
        """
        Asserts that the db_table field is correctly handled
        """
        db, table_name = self.get_model_db_table_name(self.model_def)
        self.model_def.db_table = 'test_db_table'
        self.model_def.save()
        self.assertTableDoesntExists(db, table_name)
        self.assertTableExists(db, 'test_db_table')
        self.model_def.db_table = None
        self.model_def.save()
        self.assertTableDoesntExists(db, 'test_db_table')
        self.assertTableExists(db, table_name)

    def test_fixture_loading(self):
        """
        Make model and field definitions can be loaded from fixtures.
        """
        call_command(
            'loaddata', 'fixture_loading_test', verbosity=0, commit=False
        )
        self.assertTrue(
            ModelDefinition.objects.filter(
                app_label='myfixtureapp', object_name='MyFixtureModel'
            ).exists()
        )
        model_def = ModelDefinition.objects.get(
            app_label='myfixtureapp', object_name='MyFixtureModel'
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
        Model = self.model_def.model_class()

        self.assertEqual(Model._meta.verbose_name, self.model_def.model)
        self.assertEqual(Model._meta.verbose_name_plural, "%ss" % self.model_def.model)

        self.model_def.verbose_name = 'MyMoDeL'
        self.model_def.verbose_name_plural = 'MyMoDeLZ0Rs'
        self.model_def.save()

        self.assertEqual(Model._meta.verbose_name, _('MyMoDeL'))
        self.assertEqual(Model._meta.verbose_name_plural, _('MyMoDeLZ0Rs'))

    def test_multiple_model_definition(self):
        """
        Make sure multiple model definition can coexists
        """
        other_model_def = ModelDefinition.objects.create(app_label='app',
                                                         object_name='OtherModel')
        self.assertNotEqual(other_model_def.model_class(),
                            self.model_def.model_class())
        self.assertNotEqual(other_model_def.model_ct, self.model_def.model_ct)

    def test_natural_key(self):
        natural_key = self.model_def.natural_key()
        self.assertEqual(ModelDefinition.objects.get_by_natural_key(*natural_key),
                         self.model_def)

    def test_deletion(self):
        # Add a an extra field to make sure no alter statements are issued
        CharFieldDefinition.objects.create(
            model_def=self.model_def,
            name='field',
            max_length=10
        )
        # Add a base with a field to make sure no alter statements are issued
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
        self.assertFalse(any('ALTER' in query['sql'] for query in captured_queries))
        self.assertTableDoesntExists(db, table_name)

    def test_model_management(self):
        """
        Make sure no DDL is executed when a model is marked as managed.
        """
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
            app_label='app', object_name='OtherModel',
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
            app_label='app', object_name='OtherModel',
            bases=[mixin_base, abstract_base, abstract_concrete_base],
        )
        model = model_def.model_class()
        self.assertModelTablesColumnExists(
            model, 'abstract_model_field'
        )
        self.assertModelTablesColumnDoesntExists(
            model, 'concrete_model_field'
        )
        self.assertModelTablesColumnExists(
            model, 'abstract_concrete_model_subclass_field'
        )

    def test_primary_key_override(self):
        field = CharFieldDefinition(
            name='name', max_length=32, primary_key=True
        )
        model_def = ModelDefinition.objects.create(
            fields=[field], app_label='app', object_name='OtherModel'
        )
        self.assertEqual(model_def.model_class()._meta.pk.name, field.name)

    def test_get_or_create(self):
        """
        Make sure bases and fields defaults are reaching the model initializer.
        """
        field = CharFieldDefinition(name='name', max_length=32)
        base = BaseDefinition(base=AbstractModel)
        ModelDefinition.objects.get_or_create(
            app_label='app', object_name='OtherModel',
            defaults={'bases': [base], 'fields': [field]}
        )
        self.assertIsNotNone(field.pk)
        self.assertIsNotNone(base.pk)


class ModelValidationTest(BaseModelDefinitionTestCase):
    def test_installed_app_override_failure(self):
        """
        Make sure we can't save a model definition with an app_label of
        an installed app.
        """
        self.model_def.app_label = 'mutant'
        self.assertRaises(ValidationError, self.model_def.clean)


class ModelClassProxyTest(BaseModelDefinitionTestCase):
    def test_pickling(self):
        """
        Make sure _ModelClassProxy can be pickled correctly. This is required
        to allow a model definition to subclass a MutableModel.
        """
        Model = self.model_def.model_class()
        pickled = pickle.dumps(Model)
        self.assertEqual(pickle.loads(pickled), Model)

    def test_proxy_interactions(self):
        CharFieldDefinition.objects.create(model_def=self.model_def,
                                           name="name", max_length=10)
        Model = self.model_def.model_class()
        sergei = Model.objects.create(name='Sergei')
        halak = Model(name='Halak')
        halak.save()
        self.assertTrue(issubclass(Model, models.Model))
        self.assertTrue(issubclass(Model, MutableModel))
        self.assertEqual("<class 'mutant.apps.app.models.Model'>",
                         unicode(Model))
        self.assertEqual(sergei, Model.objects.get(name='Sergei'))

        class A(object):
            class_model = Model

            def __init__(self, model):
                self.model = model

        a = A(Model)

        self.assertEqual(Model, a.model)
        self.assertEqual(Model, A.class_model)

        a.model = Model  # Assign a proxy
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

        with self.assertRaises(AttributeError):
            Model(name="name")

        with self.assertRaises(AttributeError):
            Model.objects.all()

        with self.assertRaises(ValidationError):
            instance.clean()

        with self.assertRaises(ValidationError):
            instance.save()

        with self.assertRaises(ValidationError):
            instance.delete()


class OrderingDefinitionTest(BaseModelDefinitionTestCase):
    def setUp(self):
        super(OrderingDefinitionTest, self).setUp()
        self.f1 = CharFieldDefinition.objects.create(model_def=self.model_def,
                                                     name='f1', max_length=25)
        ct_ct = ContentType.objects.get_for_model(ContentType)
        self.f2 = ForeignKeyDefinition.objects.create(model_def=self.model_def,
                                                      null=True,
                                                      name='f2', to=ct_ct)

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

    @skipUnlessMutantModelDBFeature('supports_joins')
    def test_simple_ordering(self):
        Model = self.model_def.model_class()
        model_ct = ContentType.objects.get_for_model(Model)  # app
        ct_ct = ContentType.objects.get_for_model(ContentType)  # contenttypes
        Model.objects.create(f1='Simon', f2=ct_ct)
        Model.objects.create(f1='Alexander', f2=model_ct)
        # Instances should be sorted by id
        self.assertSequenceEqual(
            Model.objects.values_list('f1', flat=True),
            ('Simon', 'Alexander')
        )
        # Instances should be sorted by f1 and not id
        f1_ordering = OrderingFieldDefinition.objects.create(model_def=self.model_def,
                                                             lookup='f1')
        self.assertSequenceEqual(
            Model.objects.values_list('f1', flat=True),
            ('Alexander', 'Simon')
        )
        # Swap the ordering to descending
        f1_ordering.descending = True
        f1_ordering.save()
        self.assertSequenceEqual(
            Model.objects.values_list('f1', flat=True),
            ('Simon', 'Alexander')
        )
        f1_ordering.delete()
        # Order by f2__app_label
        f2_ordering = OrderingFieldDefinition.objects.create(model_def=self.model_def,
                                                             lookup='f2__app_label')
        self.assertSequenceEqual(
            Model.objects.values_list('f1', flat=True),
            ('Alexander', 'Simon')
        )
        # Swap the ordering to descending
        f2_ordering.descending = True
        f2_ordering.save()
        self.assertSequenceEqual(
            Model.objects.values_list('f1', flat=True),
            ('Simon', 'Alexander')
        )
        f2_ordering.delete()

    @skipUnlessMutantModelDBFeature('supports_joins')
    def test_multiple_ordering(self):
        Model = self.model_def.model_class()
        model_ct = ContentType.objects.get_for_model(Model)  # app
        ct_ct = ContentType.objects.get_for_model(ContentType)  # contenttypes
        Model.objects.create(f1='Simon', f2=ct_ct)
        Model.objects.create(f1='Alexander', f2=model_ct)
        Model.objects.create(f1='Julia', f2=ct_ct)
        Model.objects.create(f1='Alexander', f2=ct_ct)
        # Orderings
        f1_ordering = OrderingFieldDefinition.objects.create(model_def=self.model_def,
                                                             lookup='f1')
        f2_ordering = OrderingFieldDefinition.objects.create(model_def=self.model_def,
                                                             lookup='f2__app_label')
        self.assertSequenceEqual(
            Model.objects.values_list('f1', 'f2__app_label'), (
                ('Alexander', 'app'),
                ('Alexander', 'contenttypes'),
                ('Julia', 'contenttypes'),
                ('Simon', 'contenttypes')
            )
        )
        # Swap the ordering to descending
        f2_ordering.descending = True
        f2_ordering.save()
        self.assertSequenceEqual(
            Model.objects.values_list('f1', 'f2__app_label'), (
                ('Alexander', 'contenttypes'),
                ('Alexander', 'app'),
                ('Julia', 'contenttypes'),
                ('Simon', 'contenttypes')
            )
        )
        # Swap order
        f1_ordering.order, f2_ordering.order = f2_ordering.order, f1_ordering.order
        f1_ordering.save()
        f2_ordering.save()
        self.assertSequenceEqual(
            Model.objects.values_list('f1', 'f2__app_label'), (
                ('Alexander', 'contenttypes'),
                ('Julia', 'contenttypes'),
                ('Simon', 'contenttypes'),
                ('Alexander', 'app')
            )
        )
        # Swap the ordering to descending
        f1_ordering.descending = True
        f1_ordering.save()
        self.assertSequenceEqual(
            Model.objects.values_list('f1', 'f2__app_label'), (
                ('Simon', 'contenttypes'),
                ('Julia', 'contenttypes'),
                ('Alexander', 'contenttypes'),
                ('Alexander', 'app')
            )
        )
        f1_ordering.delete()
        f2_ordering.delete()


class UniqueTogetherDefinitionTest(BaseModelDefinitionTestCase):
    def setUp(self):
        super(UniqueTogetherDefinitionTest, self).setUp()
        self.f1 = CharFieldDefinition.objects.create(model_def=self.model_def,
                                                     name='f1', max_length=25)
        self.f2 = CharFieldDefinition.objects.create(model_def=self.model_def,
                                                     name='f2', max_length=25)
        self.ut = UniqueTogetherDefinition.objects.create(model_def=self.model_def)
        self.Model = self.model_def.model_class()

    def test_repr(self):
        """
        Make sure UniqueTogetherDefinition objects are always repr()-able.
        """
        repr(self.ut)
        repr(UniqueTogetherDefinition())

    def test_clean(self):
        """
        Make sure we can't create a unique key with two fields of two
        different models
        """
        other_model_def = ModelDefinition.objects.create(app_label='app',
                                                         object_name='OtherModel')
        f2 = CharFieldDefinition.objects.create(model_def=other_model_def,
                                                name='f2', max_length=25)
        self.ut.field_defs = (self.f1, f2)
        with self.assertRaises(ValidationError):
            self.ut.clean()
        other_model_def.delete()

    def test_db_column(self):
        """
        Make sure a unique index creation works correctly when using a custom
        `db_column`. This is needed for unique FK's columns.
        """
        self.f2.db_column = 'f2_column'
        self.f2.save()
        self.ut.field_defs = (self.f1, self.f2)
        self.f2.db_column = 'f2'
        self.f2.save()
        self.ut.delete()

    def test_cannot_create_unique(self):
        """
        Creating a unique key on a table with duplicate
        rows shouldn't work
        """
        self.Model.objects.create(f1='a', f2='b')
        self.Model.objects.create(f1='a', f2='b')
        with captured_stderr():
            with self.assertRaises(IntegrityError):
                self.ut.field_defs = (self.f1, self.f2)

    def test_cannot_insert_duplicate_row(self):
        """
        Inserting a duplicate rows shouldn't work
        """
        self.Model.objects.create(f1='a', f2='b')
        self.ut.field_defs = (self.f1, self.f2)
        with captured_stderr():
            with self.assertRaises(IntegrityError):
                self.Model.objects.create(f1='a', f2='b')

    def test_cannot_remove_unique(self):
        """
        Removing a unique constraint that cause
        duplicate rows shouldn't work
        """
        self.ut.field_defs = (self.f1, self.f2)
        self.Model.objects.create(f1='a', f2='b')
        self.Model.objects.create(f1='a', f2='c')
        with captured_stderr():
            with self.assertRaises(IntegrityError):
                self.ut.field_defs.remove(self.f2)

    def test_clear_removes_unique(self):
        """
        Removing a unique constraint should relax duplicate row
        validation
        """
        self.Model.objects.create(f1='a', f2='b')
        self.ut.field_defs = self.f1, self.f2
        self.ut.field_defs.clear()
        self.Model.objects.create(f1='a', f2='b')


class BaseDefinitionTest(BaseModelDefinitionTestCase):
    def test_clean(self):
        """
        Ensure `BaseDefinition.clean` works correctly.
        """
        bd = BaseDefinition(model_def=self.model_def)
        # Base must be a class
        bd.base = BaseDefinitionTest.test_clean
        self.assertRaisesMessage(ValidationError,
                                 _('Base must be a class.'), bd.clean)
        # Subclasses of MutableModel are valid bases
        bd.base = ModelDefinition.objects.create(app_label='app',
                                                 object_name='AnotherModel').model_class()
        try:
            bd.clean()
        except ValidationError:
            self.fail('MutableModel subclasses are valid bases.')
        # But model definition can't be bases of themselves
        bd.base = self.model_def.model_class()
        self.assertRaisesMessage(ValidationError,
                                 _("A model definition can't be a base of "
                                   "itself."), bd.clean)
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
        self.assertRaisesMessage(ValidationError,
                                 _("Base can't be a proxy model."), bd.clean)

    @skipUnlessMutantModelDBFeature('supports_joins')
    def test_mutable_model_base(self):
        another_model_def = ModelDefinition.objects.create(app_label='app',
                                                           object_name='AnotherModel')
        AnotherModel = another_model_def.model_class()
        CharFieldDefinition.objects.create(model_def=self.model_def,
                                           name='f1', max_length=25)
        base_definition = BaseDefinition(model_def=another_model_def)
        base_definition.base = self.model_def.model_class()
        base_definition.save()
        another_model = AnotherModel.objects.create(f1='Martinal')
        self.assertTrue(AnotherModel.objects.exists())
        CharFieldDefinition.objects.create(model_def=self.model_def,
                                           name='f2', max_length=25, null=True)
        another_model = AnotherModel.objects.get(pk=another_model.pk)
        self.assertIsNone(another_model.f2)
        another_model.f2 = 'Placebo'
        another_model.save()

    def test_base_inheritance(self):
        Model = self.model_def.model_class()
        BaseDefinition.objects.create(model_def=self.model_def,
                                      base=Mixin)
        self.assertTrue(issubclass(Model, Mixin))
        BaseDefinition.objects.create(model_def=self.model_def,
                                      base=AbstractModel)
        self.assertTrue(issubclass(Model, Mixin) and
                        issubclass(Model, AbstractModel))

    def test_base_ordering(self):
        Model = self.model_def.model_class()
        BaseDefinition.objects.create(model_def=self.model_def,
                                      base=Mixin, order=2)
        model_subclass_def = BaseDefinition.objects.create(model_def=self.model_def,
                                                           base=AbstractModel,
                                                           order=1)
        instance = Model()
        self.assertEqual('AbstractModel', instance.method())
        model_subclass_def.order = 3
        model_subclass_def.save()
        instance = Model()
        self.assertEqual('Mixin', instance.method())

    def test_abstract_field_inherited(self):
        bd = BaseDefinition.objects.create(model_def=self.model_def,
                                           base=AbstractModel)
        Model = self.model_def.model_class()
        Model.objects.create(abstract_model_field='value')
        # Test column alteration and addition by replacing the base with
        # a new one with a field with the same name and a second field.
        bd.base = ModelSubclassWithTextField
        bd.save()
        Model.objects.get(abstract_model_field='value')
        # The original CharField should be replaced by a TextField with no
        # max_length and a second field should be added
        Model.objects.create(abstract_model_field='another one bites the dust',
                             second_field=True)
        # Test column deletion by deleting the base
        # This should cause the model to loose all it's fields and the table
        # to loose all it's columns
        bd.delete()
        self.assertEqual(list(Model.objects.values_list()),
                         [(instance.id,) for instance in Model.objects.all()])
        self.assertModelTablesColumnDoesntExists(Model, 'field')
