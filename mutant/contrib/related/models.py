
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import deletion, fields
from django.utils.translation import ugettext_lazy as _
from south.db import db as south_api

from ...db.fields import PickledObjectField, PythonIdentifierField
from ...db.models import MutableModel
from ...managers import FilteredQuerysetManager
from ...models.field import FieldDefinition
from ...models.model import ModelDefinition


related_name_help_text = _(u'The name to use for the relation from the '
                           u'related object back to this one.')

class RelatedFieldDefinition(FieldDefinition):
    
    to = fields.related.ForeignKey(ContentType, verbose_name=_(u'to'),
                                   related_name="%(app_label)s_%(class)s_to")
    
    related_name = PythonIdentifierField(_(u'related name'),
                                         blank=True, null=True,
                                         help_text=related_name_help_text)
    
    class Meta:
        app_label = 'mutant'
        abstract = True
        defined_field_options = ('related_name',)
        defined_field_category = _(u'related')
    
    @property
    def is_recursive_relationship(self):
        """
        Whether or not `to` points to this field's model definition
        """
        try:
            model_def = self.model_def
        except ModelDefinition.DoesNotExist:
            pass
        else:
            return self.to_id == model_def.contenttype_ptr_id
    
    @property
    def to_model_class_is_mutable(self):
        return issubclass(self.to.model_class(), MutableModel)
    
    def clean(self):
        if (not self.to_model_class_is_mutable and
            self.related_name is not None):
            msg = _(u'Cannot assign a related manager to non-mutable model')
            raise ValidationError({'related_name': [msg]})
    
    def get_field_options(self):
        options = super(RelatedFieldDefinition, self).get_field_options()
        
        if self.is_recursive_relationship:
            options['to'] = fields.related.RECURSIVE_RELATIONSHIP_CONSTANT
        else:
            opts = self.to.model_class()._meta
            options['to'] = "%s.%s" % (opts.app_label, opts.object_name)
            
        if not self.to_model_class_is_mutable:
            options['related_name'] = '+'
        
        return options
    
    def _south_ready_field_instance(self):
        """
        South add_column choke when passing 'self' or 'app.Model' to `to` kwarg,
        so we have to create a special version for it.
        """
        cls = self.get_field_class()
        options = self.get_field_options()
        options['to'] = self.to.model_class()
        return cls(**options)

ON_DELETE_CHOICES = (('CASCADE', _(u'CASCADE')),
                     ('PROTECT', _(u'PROTECT')),
                     ('SET_NULL', _(u'SET_NULL')),
                     ('SET_DEFAULT', _(u'SET_DEFAULT')),
                     ('SET_VALUE', _(u'SET(VALUE)')),
                     ('DO_NOTHING', _(u'DO_NOTHING')))

to_field_help_text = _(u'The field on the related object that the '
                       u'relation is to.')

on_delete_help_text = _(u'Behavior when an object referenced by this field '
                        u'is deleted')

class ForeignKeyDefinition(RelatedFieldDefinition):
    
    to_field = PythonIdentifierField(_(u'to field'), blank=True, null=True,
                                     help_text=to_field_help_text)
    
    one_to_one = fields.BooleanField(editable=False, default=False)
    
    on_delete = fields.CharField(_(u'on delete'), blank=True, null=True,
                                 choices=ON_DELETE_CHOICES, default='CASCADE',
                                 max_length=11, help_text=on_delete_help_text)
    
    on_delete_set_value = PickledObjectField(_(u'on delete set value'), null=True)
    
    objects = FilteredQuerysetManager(one_to_one=False)
    
    class Meta:
        app_label = 'mutant'
        verbose_name = _(u'foreign key')
        verbose_name_plural = _(u'foreign keys')
        defined_field_class = fields.related.ForeignKey
        defined_field_options = ('to_field',)
        
    def clean(self):
        try:
            super(ForeignKeyDefinition, self).clean()
        except ValidationError as e:
            messages = e.message_dict
        else:
            messages = {}
        
        if self.on_delete == 'SET_NULL':
            if not self.null:
                msg = _(u"This field can't be null")
                messages['on_delete'] = [msg]
        elif (self.on_delete == 'SET_DEFAULT' and
              self.default == fields.NOT_PROVIDED):
            msg = _(u'This field has no default value')
            messages['on_delete'] = [msg]
            
        if messages:
            raise ValidationError(messages)
        
    def get_field_options(self):
        options = super(ForeignKeyDefinition, self).get_field_options()
        if self.on_delete == 'SET_VALUE':
            on_delete = deletion.SET(self.on_delete_set_value)
        else:
            on_delete = getattr(deletion, self.on_delete, None)
        options['on_delete'] = on_delete
        return options

class OneToOneFieldDefinition(ForeignKeyDefinition):
    
    objects = FilteredQuerysetManager(one_to_one=True)
    
    class Meta:
        app_label = 'mutant'
        proxy = True
        verbose_name = _(u'one to one field')
        verbose_name_plural = _(u'one to one fields')
        defined_field_class = fields.related.OneToOneField
        
    def save(self, *args, **kwargs):
        self.one_to_one = True
        return super(OneToOneFieldDefinition, self).save(*args, **kwargs)

through_help_text = _(u'Intermediary model')

db_table_help_text = _(u'The name of the table to create for storing the '
                       u'many-to-many data')

class ManyToManyFieldDefinition(RelatedFieldDefinition):
    
    symmetrical = fields.NullBooleanField(_(u'symmetrical'))
    
    through = fields.related.ForeignKey(ContentType, blank=True, null=True,
                                        related_name="%(app_label)s_%(class)s_through",
                                        help_text=through_help_text)
    # TODO: This should not be a SlugField
    db_table = fields.SlugField(max_length=30, blank=True, null=True,
                                help_text=db_table_help_text)
    
    class Meta:
        app_label = 'mutant'
        verbose_name = _(u'many to many field')
        verbose_name_plural = _(u'many to many fields')
        defined_field_class = fields.related.ManyToManyField
        defined_field_options = ('symmetrical', 'through', 'db_table')

    def clean(self):
        try:
            super(ManyToManyFieldDefinition, self).clean()
        except ValidationError as e:
            messages = e.message_dict
        else:
            messages = {}
        
        if (self.symmetrical is not None and 
            not self.is_recursive_relationship):
            msg = _(u"The relationship can only be symmetrical or not if it's "
                    u"recursive, i. e. it points to 'self'")
            messages['symmetrical'] = [msg]
        
        if self.through:
            if self.db_table:
                msg = _(u'Cannot specify a db_table if an intermediate '
                        u'model is used.')
                messages['db_table'] = [msg]
        
            if self.symmetrical:
                msg = _(u'Many-to-many fields with intermediate model cannot '
                        u'be symmetrical.')
                messages.setdefault('symmetrical', []).append(msg)
            
            seen_from, seen_to = 0, 0
            to_model = self.to.model_class()  
            through_class = self.through.model_class()
            from_model = self.model_def.cached_model
            for field in through_class._meta.fields:
                rel_to = getattr(field.rel, 'to', None)
                if rel_to == from_model:
                    seen_from += 1
                elif rel_to == to_model:
                    seen_to += 1
            if self.is_recursive_relationship():
                if seen_from > 2:
                    msg = _(u'Intermediary model %s has more than two foreign '
                            u'keys to %s, which is ambiguous and is not permitted.')
                    formated_msg = msg % (through_class._meta.object_name,
                                          from_model._meta.object_name)
                    messages.setdefault('through', []).append(formated_msg)
            else:
                msg = _(u'Intermediary model %s has more than one foreign key '
                        u' to %s, which is ambiguous and is not permitted.')
                if seen_from > 1:
                    formated_msg = msg % (through_class._meta.object_name,
                                          from_model._meta.object_name)
                    messages.setdefault('through', []).append(formated_msg)
                if seen_to > 1:
                    formated_msg = msg % (through_class._meta.object_name,
                                          to_model._meta.object_name)
                    messages.setdefault('through', []).append(formated_msg)
                
        if messages:
            raise ValidationError(messages)
        
    def save(self, *args, **kwargs):
        create = not self.pk
        
        save = super(ManyToManyFieldDefinition, self).save(*args, **kwargs)
        model = self.model_def.model_class()
        field = model._meta.get_field(str(self.name))
        intermediary_model = field.rel.through
        
        # TODO: Make sure to delete the intermediary table if through is changed
        # to an existing model
        if create:
            if self.through is None:
                opts = intermediary_model._meta
                fields = tuple((field.name, field) for field in opts.fields)
                south_api.create_table(opts.db_table, fields)
        else:
            #TODO: look for db_table rename
            pass
        
        return save

