
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import models
from django.db.utils import IntegrityError

from mutant.models.model import (ModelDefinition, OrderingFieldDefinition,
    UniqueTogetherDefinition, BaseDefinition)
from mutant.contrib.text.models import CharFieldDefinition
from mutant.contrib.related.models import ForeignKeyDefinition
from mutant.db.models import MutableModel
from mutant.tests.models.utils import BaseModelDefinitionTestCase


class ModelDefinitionManipulationTest(BaseModelDefinitionTestCase):
    
    def test_model_class_creation_cache(self):
        Member = self.model_def.model_class()
        self.assertEqual(Member, self.model_def.model_class())
        
        self.assertNotEqual(Member, self.model_def.model_class(force_create=True))

    def test_rename_model(self):
        """
        Make sure changing the app_label or object_name renames the associated
        table
        """
        def get_table_name():
            return self.model_def.model_class()._meta.db_table
        
        table_name = get_table_name()
        self.model_def.app_label = 'myapp'
        self.model_def.save()
        self.assertTableDoesntExists(table_name)
        table_name = get_table_name()
        self.assertTableExists(table_name)
        
        self.model_def.object_name = 'MyModel'
        self.model_def.save()
        self.assertTableDoesntExists(table_name)
        table_name = get_table_name()
        self.assertTableExists(table_name)
        
        self.model_def.delete()
        self.assertTableDoesntExists(table_name)
        
    def test_fixture_loading(self):
        call_command('loaddata', 'fixture_loading_test', verbosity=0, commit=False)
        model_def = ModelDefinition.objects.get(app_label='myfixtureapp',
                                                object_name='MyFixtureModel')
        Model = model_def.model_class()
        Model.objects.create()
            
class ModelValidationTest(BaseModelDefinitionTestCase):
    
    def test_installed_app_override_failure(self):
        """
        Make sure we can't save a model definition with an app_label of
        an installed app.
        """
        self.model_def.app_label = 'mutant'
        self.assertRaises(ValidationError, self.model_def.clean)

class ModelClassProxyProxyTests(BaseModelDefinitionTestCase):
    
    def test_proxy_interactions(self):
        CharFieldDefinition.objects.create(model_def=self.model_def,
                                           name="name", max_length=10)
        Model = self.model_def.model_class()
        
        sergei = Model.objects.create(name='Sergei')
        
        halak = Model(name='Halak')
        halak.save()
        
        assert issubclass(Model, models.Model)
        
        assert unicode(Model) == u"<class 'mutant.apps.app.models.Model'>"
        
        assert sergei == Model.objects.get(name='Sergei')
        
        class A(object):
            
            class_model = Model
            
            def __init__(self, model):
                self.model = model
        
        a = A(Model)
        
        assert Model == a.model
        assert Model == A.class_model
        
        a.model = Model # Assign a proxy
        a.model = a.model # Assign a Model
        a.model = 4

    def test_definition_deletion(self):
        CharFieldDefinition.objects.create(model_def=self.model_def,
                                           name="name", max_length=10)
        
        Model = self.model_def.model_class()
        instance = Model.objects.create(name="Quebec")
        table_name = Model._meta.db_table
        self.model_def.delete()
        self.assertTableDoesntExists(table_name)
        
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
            
        self.setUp() # Recreate the model definition to delete it in tearDown

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
        
        ordering.lookup = '?'
        ordering.clean()
        
        ordering.lookup = 'f1'
        ordering.clean()
        
        ordering.lookup = 'f2__app_label'
        ordering.clean()
        
        with self.assertRaises(ValidationError):
            ordering.lookup = 'f3'
            ordering.clean()
            
        with self.assertRaises(ValidationError):
            ordering.lookup = 'f2__higgs_boson'
            ordering.clean()

    def test_simple_ordering(self):
        Model = self.model_def.model_class()
        model_ct = ContentType.objects.get_for_model(Model) #app
        ct_ct = ContentType.objects.get_for_model(ContentType) #contenttypes
        Model.objects.create(f1='Simon', f2=ct_ct)
        Model.objects.create(f1='Alexander', f2=model_ct)
        
        
        # Instances should be sorted by id
        self.assertQuerysetEqual(Model.objects.values('f1'),
                                 [u'Simon', u'Alexander'],
                                 transform=lambda x: x['f1'], ordered=True)
        
        # Instances should be sorted by f1 and not id
        f1_ordering = OrderingFieldDefinition.objects.create(model_def=self.model_def,
                                                             lookup='f1')
        self.assertQuerysetEqual(Model.objects.values('f1'),
                                 [u'Alexander', u'Simon'],
                                 transform=lambda x: x['f1'], ordered=True)
        
        # Swap the ordering to descending
        f1_ordering.descending = True
        f1_ordering.save()
        self.assertQuerysetEqual(Model.objects.values('f1'),
                                 [u'Simon', u'Alexander'],
                                 transform=lambda x: x['f1'], ordered=True)
        f1_ordering.delete()
        
        # Order by f2__app_label
        f2_ordering = OrderingFieldDefinition.objects.create(model_def=self.model_def,
                                                             lookup='f2__app_label')
        self.assertQuerysetEqual(Model.objects.values('f1'),
                                 [u'Alexander', u'Simon'],
                                 transform=lambda x: x['f1'], ordered=True)
        
        # Swap the ordering to descending
        f2_ordering.descending = True
        f2_ordering.save()
        self.assertQuerysetEqual(Model.objects.values('f1'),
                                 [u'Simon', u'Alexander'],
                                 transform=lambda x: x['f1'], ordered=True)
        f2_ordering.delete()
    
    def test_multiple_ordering(self):
        Model = self.model_def.model_class()
        model_ct = ContentType.objects.get_for_model(Model) #app
        ct_ct = ContentType.objects.get_for_model(ContentType) #contenttypes
        Model.objects.create(f1='Simon', f2=ct_ct)
        Model.objects.create(f1='Alexander', f2=model_ct)
        Model.objects.create(f1='Julia', f2=ct_ct)
        Model.objects.create(f1='Alexander', f2=ct_ct)
        
        f1_ordering = OrderingFieldDefinition.objects.create(model_def=self.model_def,
                                                             lookup='f1')
        f2_ordering = OrderingFieldDefinition.objects.create(model_def=self.model_def,
                                                             lookup='f2__app_label')
        
        
        self.assertQuerysetEqual(Model.objects.values('f1', 'f2__app_label'),
                                 [(u'Alexander', u'app'), (u'Alexander', u'contenttypes'),
                                  (u'Julia', u'contenttypes'), (u'Simon', u'contenttypes')],
                                 transform=lambda x: (x['f1'], x['f2__app_label']),
                                 ordered=True)
        
        # Swap the ordering to descending
        f2_ordering.descending = True
        f2_ordering.save()
        self.assertQuerysetEqual(Model.objects.values('f1', 'f2__app_label'),
                                 [(u'Alexander', u'contenttypes'), (u'Alexander', u'app'),
                                  (u'Julia', u'contenttypes'), (u'Simon', u'contenttypes')],
                                 transform=lambda x: (x['f1'], x['f2__app_label']),
                                 ordered=True)
        
        # Swap order
        f1_ordering.order, f2_ordering.order = f2_ordering.order, f1_ordering.order
        f1_ordering.save()
        f2_ordering.save()
        self.assertQuerysetEqual(Model.objects.values('f1', 'f2__app_label'),
                                 [(u'Alexander', u'contenttypes'), (u'Julia', u'contenttypes'),
                                  (u'Simon', u'contenttypes'), (u'Alexander', u'app')],
                                 transform=lambda x: (x['f1'], x['f2__app_label']),
                                 ordered=True)
        
        # Swap the ordering to descending
        f1_ordering.descending = True
        f1_ordering.save()
        self.assertQuerysetEqual(Model.objects.values('f1', 'f2__app_label'),
                                 [(u'Simon', u'contenttypes'), (u'Julia', u'contenttypes'),
                                  (u'Alexander', u'contenttypes'), (u'Alexander', u'app')],
                                 transform=lambda x: (x['f1'], x['f2__app_label']),
                                 ordered=True)
        
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

    def test_clean(self):
        """
        Make sure we can't create a unique key with two fields of two
        different models
        """
        other_model_def = ModelDefinition.objects.create(app_label='app',
                                                         object_name='OtherModel')
        
        #TODO: move that somewhere else
        assert other_model_def.model_class() != self.model_def.model_class()
        assert other_model_def.model_ct != self.model_def.model_ct
        
        f2 = CharFieldDefinition.objects.create(model_def=other_model_def,
                                                name='f2', max_length=25)
        self.ut.field_defs.add(self.f1, f2)
        with self.assertRaises(ValidationError):
            self.ut.clean()
        other_model_def.delete()

    def test_cannot_create_unique(self):
        """
        Creating a unique key on a table with duplicate 
        rows shouldn't work
        """
        self.Model.objects.create(f1='a', f2='b')
        self.Model.objects.create(f1='a', f2='b')
        with self.assertRaises(IntegrityError):
            self.ut.field_defs.add(self.f1, self.f2)
    
    def test_cannot_insert_duplicate_row(self):
        """
        Inserting a duplicate rows shouldn't work
        """
        self.Model.objects.create(f1='a', f2='b')
        self.ut.field_defs.add(self.f1, self.f2)
        with self.assertRaises(IntegrityError):
            self.Model.objects.create(f1='a', f2='b')
    
    def test_cannot_remove_unique(self):
        """
        Removing a unique constraint that cause 
        duplicate rows shouldn't work
        """
        self.ut.field_defs.add(self.f1, self.f2)
        self.Model.objects.create(f1='a', f2='b')
        self.Model.objects.create(f1='a', f2='c')
        with self.assertRaises(IntegrityError):
            self.ut.field_defs.remove(self.f2)

    def test_clear_removes_unique(self):
        """
        Removing a unique constraint should relax duplicate row
        validation
        """
        self.Model.objects.create(f1='a', f2='b')
        self.ut.field_defs.add(self.f1, self.f2)
        self.ut.field_defs.clear()
        self.Model.objects.create(f1='a', f2='b')
    
class Mixin(object):
    
    def method(self):
        return 'Mixin'

class ModelProxy(CharFieldDefinition):
    
    class Meta:
        proxy = True

class ModelSubclass(models.Model):
    
    field = models.CharField(max_length=5)
    
    class Meta:
        abstract = True
    
    def method(self):
        return 'ModelSubclass'
    
class ModelSubclassWithTextField(models.Model):
    
    field = models.TextField()
    second_field = models.NullBooleanField()
    
    class Meta:
        abstract = True

class MutableModelSubclass(MutableModel):
    pass
        
class BaseDefinitionTest(BaseModelDefinitionTestCase):
    
    def test_clean(self):
        bd = BaseDefinition()
        
        # Base must be a class
        bd.base = BaseDefinitionTest.test_clean
        self.assertRaises(ValidationError, bd.clean)
        
        # Subclasses of MutableModel are not valid bases
        bd.base = MutableModelSubclass
        self.assertRaises(ValidationError, bd.clean)
        
        # Mixin objets are valid bases
        bd.base = Mixin
        bd.clean()

        # Model subclasses are valid bases if they are abstract
        bd.base = ModelSubclass
        bd.clean()
        
        # Model subclasses that are not abstract are invalid
        bd.base = CharFieldDefinition
        self.assertRaises(ValidationError, bd.clean)
        bd.base = ModelProxy
        self.assertRaises(ValidationError, bd.clean)
    
    def test_base_inheritance(self):
        Model = self.model_def.model_class()
        
        BaseDefinition.objects.create(model_def=self.model_def,
                                      base=Mixin)
        self.assertTrue(issubclass(Model, Mixin))
        
        BaseDefinition.objects.create(model_def=self.model_def,
                                      base=ModelSubclass)
        self.assertTrue(issubclass(Model, Mixin) and
                        issubclass(Model, ModelSubclass))
    
    def test_base_ordering(self):
        Model = self.model_def.model_class()
        
        BaseDefinition.objects.create(model_def=self.model_def,
                                      base=Mixin, order=2)
        model_subclass_def = BaseDefinition.objects.create(model_def=self.model_def,
                                                           base=ModelSubclass,
                                                           order=1)
        
        instance = Model()
        self.assertEqual('ModelSubclass', instance.method())
        
        model_subclass_def.order = 3
        model_subclass_def.save()
        instance = Model()
        self.assertEqual('Mixin', instance.method())
        
    def test_abstract_field_inherited(self):
        bd = BaseDefinition.objects.create(model_def=self.model_def,
                                           base=ModelSubclass)
        
        Model = self.model_def.model_class()
        
        Model.objects.create(field='value')
        
        # Test column alteration and addition by replacing the base with
        # a new one with a field with the same name and a second field.
        bd.base = ModelSubclassWithTextField
        bd.save()
        Model.objects.get(field='value')
        # The original CharField should be replaced by a TextField with no
        # max_length and a second field should be added
        Model.objects.create(field='another one bites the dust',
                             second_field=True)
        
        # Test column deletion by deleting the base
        # This should cause the model to loose all it's fields and the table
        # to loose all it's columns
        bd.delete()
        self.assertEqual(list(Model.objects.values_list()), [(1,), (2,)])
        self.assertFieldDoesntExists(Model._meta.db_table, 'field')
