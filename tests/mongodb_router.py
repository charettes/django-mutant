
class MongoRouter(object):
    
    def _db_for(self, model, **hints):
        from mutant.db.models import MutableModel
        if issubclass(model, MutableModel):
            return 'mongo'
        else:
            return 'default'
    
    db_for_read = _db_for
    
    db_for_write = _db_for

    def allow_syncdb(self, db, model):
        return self._db_for(model) == db
