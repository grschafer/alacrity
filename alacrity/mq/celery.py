from __future__ import absolute_import
from celery import Celery

celery = Celery('alacrity.mq.celery')
# https://groups.google.com/forum/#!topic/celery-users/D-5PtgAqdLI
# https://github.com/celery/celery/issues/1407
celery.config_from_object('alacrity.mq.celeryconfig:')

if __name__ == '__main__':
    celery.start()
