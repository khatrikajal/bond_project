# routers/database_router.py

class HybridDatabaseRouter:
    """
    Hybrid router that supports both app-level and model-level routing.
    
    Priority:
    1. Model-level (DATABASE attribute on model) - HIGHEST PRIORITY
    2. App-level (route_app_labels) - FALLBACK
    3. Default Django behavior - if neither specified
    
    Usage Examples:
    
    # App-level routing (all models in app use same DB):
    route_app_labels = {
        'users': 'default',      # All models in 'users' app → default DB
        'inventory': 'secondary' # All models in 'inventory' app → secondary DB
    }
    
    # Model-level routing (specific model overrides):
    class MyModel(models.Model):
        DATABASE = 'secondary'  # This specific model uses secondary DB
        # ... fields
    """
    
    # ============================================
    # CONFIGURATION: Define your app-level routing here
    # ============================================
    route_app_labels = {
        # Django built-in apps (usually on default)
        'authentication': 'default',
        'kyc': 'default',
        # 'sessions': 'default',
        # 'admin': 'default',
        
        # # Your custom apps
        # 'users': 'default',
        # 'accounts': 'default',
        
        # Apps using secondary database
        'bonds': 'transformation',
        # 'analytics': 'secondary',
        # 'logs': 'secondary',
    }
    
    def db_for_read(self, model, **hints):
        """
        Determine which database to use for read operations.
        Checks model-level DATABASE attribute first, then app-level routing.
        """
        # Priority 1: Check if model has DATABASE attribute (model-level routing)
        if hasattr(model, 'DATABASE'):
            return model.DATABASE
        
        # Priority 2: Check app-level routing
        if model._meta.app_label in self.route_app_labels:
            return self.route_app_labels[model._meta.app_label]
        
        # Priority 3: Return None to use Django's default behavior
        return None
    
    def db_for_write(self, model, **hints):
        """
        Determine which database to use for write operations.
        Same priority as read operations.
        """
        # Priority 1: Model-level routing
        if hasattr(model, 'DATABASE'):
            return model.DATABASE
        
        # Priority 2: App-level routing
        if model._meta.app_label in self.route_app_labels:
            return self.route_app_labels[model._meta.app_label]
        
        # Priority 3: Default behavior
        return None
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Determine if a relationship between two objects is allowed.
        Only allow relations between objects in the same database.
        """
        db_obj1 = self._get_db_for_model(obj1._meta.model)
        db_obj2 = self._get_db_for_model(obj2._meta.model)
        
        # If both objects have a database assigned
        if db_obj1 and db_obj2:
            # Only allow relation if they're in the same database
            return db_obj1 == db_obj2
        
        # If we can't determine, return None (let Django decide)
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Determine if migration should run on a given database.
        Ensures models only migrate to their designated database.
        """
        # Priority 1: Check model-level DATABASE attribute
        if model_name:
            model = hints.get('model')
            if model and hasattr(model, 'DATABASE'):
                # Only allow migration if db matches model's DATABASE
                return db == model.DATABASE
        
        # Priority 2: Check app-level routing
        if app_label in self.route_app_labels:
            # Only allow migration if db matches app's database
            return db == self.route_app_labels[app_label]
        
        # Priority 3: Default - allow migration on default database only
        # This prevents unrouted apps from migrating to all databases
        return db == 'default'
    
    def _get_db_for_model(self, model):
        """
        Helper method to get database for a model.
        Follows same priority: model-level > app-level > None
        """
        if hasattr(model, 'DATABASE'):
            return model.DATABASE
        
        if model._meta.app_label in self.route_app_labels:
            return self.route_app_labels[model._meta.app_label]
        
        return None


