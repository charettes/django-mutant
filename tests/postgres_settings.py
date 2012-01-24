
from test_project.settings import * #@UnusedWildImport

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'mutant',                      # Or path to database file if using sqlite3.
        'USER': 'mutant',                      # Not used with sqlite3.
        'PASSWORD': 'mutant',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}
