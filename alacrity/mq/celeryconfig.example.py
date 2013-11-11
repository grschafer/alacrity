BROKER_URL = CELERY_RESULT_BACKEND = \
        'transport://userid:password@hostname:port/virtual_host'

CELERY_IMPORTS = ['alacrity.mq.tasks']

CELERY_TASK_SERIALIZER = 'json' # default: 'pickle'
CELERY_RESULT_SERIALIZER = 'json' # default: 'pickle'

# long-running tasks, so we want them to spread evenly among workers
CELERYD_PREFETCH_MULTIPLIER = 1 # default: 4

#CELERY_TIMEZONE = 'US/Mountain' # requires pytz
#CELERY_ENABLE_UTC = True

from datetime import timedelta
CELERYBEAT_SCHEDULE = {
    'add-every-30-seconds': {
        'task': 'alacrity.mq.tasks.add',
        'schedule': timedelta(seconds=30),
        'args': (16, 16)
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
EMAIL_USE_TLS = True
