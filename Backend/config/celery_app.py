import os

from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("cockpit")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.update(
    worker_pool="eventlet",  # Use eventlet pool
    worker_max_tasks_per_child=100,
    broker_pool_limit=10,
)

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
