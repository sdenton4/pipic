from __future__ import absolute_import

import os

from celery import Celery
from datetime import timedelta

from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djpilapse.settings')

app = Celery('proj',
             broker='amqp://',
             backend='amqp://',
             include=['djpilapp.tasks'])

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
"""
app.conf.update(
    CELERY_RESULT_BACKEND='djcelery.backends.database:DatabaseBackend',
)
"""
app.conf.update(
    CELERY_RESULT_BACKEND='djcelery.backends.cache:CacheBackend',
    CELERYBEAT_SCHEDULE = {
    'add-every-6-seconds': {
        'task': 'tasks.add',
        'schedule': timedelta(seconds=6),
        'args': (16, 16),
    }},
    CELERY_TIMEZONE = 'UTC',
)

# Optional configuration, see the application user guide.
app.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
)

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

CELERYBEAT_SCHEDULER = "djcelery.schedulers.DatabaseScheduler"




if __name__ == '__main__':
    app.start()


