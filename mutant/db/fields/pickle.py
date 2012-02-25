
from picklefield.fields import PickledObjectField as _PickledObjectField


class _ObjectWrapper(object):
    __slots__ = ('_obj',)
    
    def __init__(self, obj):
        self._obj = obj

class PickledObjectField(_PickledObjectField):
    
    def to_python(self, value):
        value = super(PickledObjectField, self).to_python(value)
        if isinstance(value, _ObjectWrapper):
            value = value._obj
        return value
    
    def pre_save(self, model_instance, add):
        value = super(PickledObjectField, self).pre_save(model_instance, add)
        if hasattr(value, 'prepare_database_save'):
            value = _ObjectWrapper(value)
        return value
