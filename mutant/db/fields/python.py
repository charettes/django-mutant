import os
import re
import types

from django.core.exceptions import ValidationError
from django.db.models.fields import CharField
from django.utils.encoding import smart_unicode
from django.utils.importlib import import_module
from django.utils.translation import ugettext_lazy as _

from mutant.validators import (validate_python_identifier,
    validate_python_object_path)

class DirectoryPathField(CharField):
    
    def to_python(self, value):
        value = super(DirectoryPathField, self).to_python(value)
        if value is None:
            return
        if not os.path.exists(value):
            raise ValidationError(_(u"Specified path doesn't exist"))
        elif not os.path.isdir(value):
            raise ValidationError(_(u"Specified path isn't a directory"))
        else:
            return value

class RegExpStringField(CharField):
    
    def to_python(self, value):
        value = super(RegExpStringField, self).to_python(value)
        if value is None:
            return
        try:
            re.compile(value)
        except Exception as e:
            raise ValidationError(_(e))
        else:
            return value

class PythonIdentifierField(CharField):
    default_validators = [validate_python_identifier]
    description = _(u'Python identifier')
    empty_strings_allowed = False

    def __init__(self, *args, **kwargs):
        defaults = {'max_length': 255}
        defaults.update(kwargs)
        super(PythonIdentifierField, self).__init__(*args, **defaults)

class PythonObjectReferenceField(CharField):
    description = _(u'Referencable python object')
    empty_strings_allowed = False
    
    class reference(tuple):
        
        def __new__(cls, *args):
            if (len(args) != 2):
                raise TypeError('reference takes 2 arguments')
            if not all(isinstance(arg, str) or arg is None for arg in args):
                raise TypeError('reference takes 2 str as arguments')
            try:
                validate_python_object_path('.'.join(arg for arg in args if arg is not None))
            except ValidationError:
                raise TypeError("Specified arguments aren't a valid "
                                "python object reference.")
                
            return tuple.__new__(cls, args)
    
        @property
        def module(self):
            return self[0]
    
        @property
        def name(self):
            return self[1]
    
        @property
        def obj(self):
            module = import_module(self.module)
            if self.name:
                try:
                    obj = getattr(module, self.name)
                except AttributeError:
                    msg = "Cannot import name {1} from {0}".format(*self)
                    raise ImportError(msg)
            else:
                obj = module
            return obj
            
        def __str__(self):
            return "{0}.{1}".format(*self)

    def __init__(self, *args, **kwargs):
        self.allowed_types = kwargs.pop('allowed_types', ())
        if kwargs.get('null', False):
            self.allowed_types += (types.NoneType,)
        defaults = {'max_length': 255}
        defaults.update(kwargs)
        super(PythonObjectReferenceField, self).__init__(*args, **defaults)

    def _get_object_import_path(self, obj):
        if type(obj) == types.ModuleType:
            return tuple(obj.__name__.rsplit('.', 1))
        try:
            module = getattr(obj, '__module__')
            name = getattr(obj, '__name__')
        except AttributeError:
            msg = "The object {0} cannot be referenced from a python path"
            raise ValidationError(msg.format(obj))
        else:
            return (module, name)
    
    def to_python(self, value):
        if isinstance(value, self.reference) or value is None:
            pass
        elif isinstance(value, basestring):
            if '.' in value:
                module, name = value.rsplit('.', 1)
            else:
                # We can reference a module
                module, name = value, None
            value = self.reference(module, name)
        elif isinstance(value, tuple):
            # We might have a ('path.to.module', 'obj') tuple
            value = self.reference(*value)
        else:
            return self.to_python(self._get_object_import_path(value))
        
        if value is not None:
            obj = value.obj
        else:
            obj = None
        obj_type = type(obj)
        if obj_type in self.allowed_types:
            return value
        else:
            msg = "The object {0}'s type '{1}' isn't allowed for this field."
            raise ValidationError(msg.format(obj, obj_type.__name__))

    def get_prep_value(self, value):
        if value is None:
            return value
        return smart_unicode(u"{0}.{1}".format(value.__module__,
                                               value.__name__))

