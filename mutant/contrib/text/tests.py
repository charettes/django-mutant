# -*- coding: utf-8 -*-

from django.db import connection
from django.db.utils import DatabaseError
from django.utils.unittest.case import skipUnless

from ...test.testcases import FieldDefinitionTestMixin
from ...tests.models.utils import BaseModelDefinitionTestCase

from .models import CharFieldDefinition, TextFieldDefinition


class CharFieldDefinitionTest(FieldDefinitionTestMixin,
                              BaseModelDefinitionTestCase):
    field_definition_cls = CharFieldDefinition
    field_defintion_init_kwargs = {'max_length': 255}
    field_values = ('Raptor Jesus', 'Nirvana')
    
    @skipUnless(connection.settings_dict['ENGINE'] != 'django.db.backends.sqlite3',
                "Skipping because sqlite3 doesn't enforce CHAR length")
    def test_field_max_length(self):
        self.field.max_length = 24
        self.field.save()
        Model = self.model_def.model_class()
        with self.assertRaises(DatabaseError):
            Model.objects.create(field='Simon' * 5)

class TextFieldDefinitionTest(FieldDefinitionTestMixin,
                              BaseModelDefinitionTestCase):
    field_definition_cls = TextFieldDefinition
    field_values = (
        u"""
        J'ai caché
        Mieux que partout ailleurs
        Au grand jardin de mon coeur
        Une petite fleur
        Cette fleur
        Plus jolie qu'un bouquet
        Elle garde en secret
        Tous mes rêves d'enfant
        L'amour de mes parents
        Et tous ces clairs matins
        Fait d'heureux souvenirs lointains
        """,
        
        u"""
        Quand la vie
        Par moments me trahi
        Tu restes mon bonheur
        Petite fleur
        
        Sur mes vingt ans
        Je m'arrête un moment
        Pour respirer
        Le parfum que j'ai tant aimé
        
        Dans mon coeur
        Tu fleuriras toujours
        Au grand jardin d'amour
        Petite fleur
        """,
    )
