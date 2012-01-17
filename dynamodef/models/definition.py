
from django.db import models

class CachedObjectDefinition(models.Model):
    
    __cache = {}
    
    class Meta:
        abstract = True
    
    @classmethod
    def clear_cache(cls):
        cls.__cache = {}
    
    def invalidate_definition(self):
        """
        Pop a defined object from the cache defaulting to none
        """
        cache_access = self._get_cache_access()
        if cache_access:
            cache, key = cache_access
            return cache.pop(key, None)
    
    def _get_cache_access(self):
        """
        Provide cache access if available
        """
        if self.pk:
            cls = self.__class__
            return cls.__cache, (cls, self.pk)
    
    def _get_object_definition(self):
        raise NotImplementedError
    
    def _prepare_object_definition(self, obj):
        return obj
    
    @property
    def defined_object(self):
        """
        Provide the defined object and cache it if possible
        """
        cache_access = self._get_cache_access()
        if cache_access:
            cache, key = cache_access
            if key not in cache:
                cache[key] = self._get_object_definition()
            obj = cache[key]
        else:
            obj = self._get_object_definition()
        return self._prepare_object_definition(obj)
        
    def save(self, *args, **kwargs):
        """
        Save the model instance while making sure the definition is invalidated
        """
        self.invalidate_definition()
        return super(CachedObjectDefinition, self).save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """
        Delete the model instance while making sure the definition is invalidated
        """
        self.invalidate_definition()
        return super(CachedObjectDefinition, self).delete(*args, **kwargs)
