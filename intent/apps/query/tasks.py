from celery.task import task
from celery.task import periodic_task
from django.core.cache import cache
from time import sleep

from datetime import timedelta
from celery.decorators import task, periodic_task

from intent.apps.core.utils import *

from .models import *

# Run this
# python manage.py celeryd -E -B --loglevel=INFO

def single_instance_task(timeout):
    def task_exc(func):
        def wrapper(*args, **kwargs):
            lock_id = "celery-single-instance-" + func.__name__
            acquire_lock = lambda: cache.add(lock_id, "true", timeout)
            release_lock = lambda: cache.delete(lock_id)
            if acquire_lock():
                try:
                    func(*args, **kwargs)
                finally:
                    release_lock()
        return wrapper
    return task_exc

@periodic_task(run_every=timedelta(seconds=2))
#@single_instance_task(60*10)
def add_to_count():
    logger = add_to_count.get_logger()
    try:
        sc = SampleCount.objects.get(pk = 1)
        if sc:
            sc.num += 1
            sc.save()
            logger.info("Incremented %s" % (sc.num))
        else:
            logger.error("Unable to get pk=1 for SampleCount")
    except Exception, e:
        logger.error("Exception while executing add_to_count task asynchronously. %s" % e)
        raise e

LOCK_EXPIRE = 60 * 5 # Lock expires in 5 minutes
@periodic_task(run_every = timedelta(seconds=2))
def test():
    lock_id = "lock"

    # cache.add fails if if the key already exists
    acquire_lock = lambda: cache.add(lock_id, "true", LOCK_EXPIRE)
    # memcache delete is very slow, but we have to use it to take
    # advantage of using add() for atomic locking
    release_lock = lambda: cache.delete(lock_id)

    if acquire_lock():
        try:
            print 'pre'
            sleep(20)
            print 'post'
        finally:
            release_lock()
        return
    print 'already in use...'