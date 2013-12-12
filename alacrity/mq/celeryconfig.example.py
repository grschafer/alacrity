from __future__ import absolute_import
from datetime import timedelta
from celery.schedules import crontab

BROKER_URL = CELERY_RESULT_BACKEND = \
        'transport://userid:password@hostname:port/virtual_host'

CELERY_IMPORTS = ['alacrity.mq.tasks']

#CELERY_TASK_SERIALIZER = 'json' # default: 'pickle'
#CELERY_RESULT_SERIALIZER = 'json' # default: 'pickle'

# remove results and result queues 1 hour after completion
# shouldn't affect groups/chains even if worker is held up
# because the results of one step are stored as arguments of the next
#CELERY_TASK_RESULT_EXPIRES = 30 # time in seconds or timedelta

#CELERY_IGNORE_RESULT = True # need results for .get() and chords?

# long-running tasks, so we want them to spread evenly among workers
CELERYD_PREFETCH_MULTIPLIER = 1 # default: 4

#CELERY_TIMEZONE = 'US/Mountain' # requires pytz
CELERY_ENABLE_UTC = True

#CELERY_DEFAULT_RATE_LIMIT = '1/m'

CELERYBEAT_SCHEDULE = {
        'find new matches': {
            'task': 'alacrity.mq.tasks.workflow',
            'schedule': crontab(minute=16, hour=21),
        },
        'update leagues': {
            'task': 'alacrity.mq.tasks.update_leagues',
            'schedule': crontab(minute=39, hour=20),
        },
}

CELERY_SEND_TASK_ERROR_EMAILS = True

ADMINS = [('Name', 'name@example.com')]

# Email address used as sender (From field).
SERVER_EMAIL = "celery@example.com"

# Mailserver configuration
EMAIL_HOST = "smtp.example.com"
EMAIL_PORT = 25
EMAIL_HOST_USER = "username"
EMAIL_HOST_PASSWORD = "password"
EMAIL_USE_SSL = True
#EMAIL_USE_TLS = True
