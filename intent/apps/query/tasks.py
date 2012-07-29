from celery.task import task
from celery.task import periodic_task
from django.core.cache import cache
from time import sleep

from datetime import timedelta, datetime
from celery.decorators import periodic_task

from django.utils import timezone
from django.utils.timezone import utc

from .utils import run_and_analyze_query, lookup_rules_in_db_for_intents
from intent.apps.query.models import Rule, Author, Query, Document

from intent.apps.core.utils import *

# Run this
# python manage.py celeryd -E -B --loglevel=INFO

def log_exception(logger, message=''):
    '''
    logs stacktrace with function name.
    usage:
        import traceback
        log_exception(message='some message goes here')
    '''
    exc_type, exc_value, exc_traceback = sys.exc_info()
    lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    lines.append(message)
    logger.error(''.join('!! ' + line for line in lines))  # Log it or whatever here

@periodic_task(run_every=timedelta(minutes=1))
def run_and_analyze_queries():
    try:
        task_logger = run_and_analyze_queries.get_logger()

        queries = [query for query in Query.objects.filter(status=Query.WAITING_TO_RUN_STATUS)]
        task_logger.info("    Queries to run = %d" % len(queries))
        for query in queries:
            try:
                task_logger.info("    Running query %s for user %s" % (query.query, query.created_by))
                query.status = Query.RUNNING_STATUS
                query.save()
                tweets, wants, questions, promises = run_and_analyze_query(query.query, query.count)

                # For each analyzed tweet, add a document
                for tweet in tweets:

                    try:
                        document = Document.objects.get(source_id = tweet['tweet_id'])
                    except Document.DoesNotExist:
                        document = None

                    if not document:
                        author = Author.objects.create(twitter_handle=tweet['author'], name='')
                        author.save()
                        rules = lookup_rules_in_db_for_intents(tweet['intents'])

                        document = Document.objects.create(
                            result_of=query,
                            source=Document.TWITTER_SOURCE,
                            author=author,
                            source_id = tweet['tweet_id'],
                            date=tweet['date'],
                            analyzed=True,
                            want_rule=rules['want_rule'],
                            promise_rule=rules['promise_rule'],
                            question_rule=rules['question_rule'],
                            dislike_rule=rules['dislike_rule'],
                        )
                        document.save()
                    else:
                        # We have already analyzed this tweeet. may be we ran soon. SKIP
                        task_logger.info("    already analyzed tweeet. may be we ran soon. SKIPPING (%s)" % tweet['content'])

                query.status = Query.WAITING_TO_RUN_STATUS
                query.last_run = datetime.utcnow().replace(tzinfo=utc)
                query.num_times_run += 1
                query.save()

            except Exception, e:
                log_exception(task_logger, "Exception while processing query %s for user %s" % (query.query, query.created_by))
                query.status = Query.WAITING_TO_RUN_STATUS
                query.last_run = datetime.utcnow().replace(tzinfo=utc)
                query.num_times_run += 1
                query.query_exception = e.message
                query.save()

            task_logger.info("    Processed query %s for user %s" % (query.query, query.created_by))
    except Exception, e:
        log_exception(task_logger, "Exception while executing run_and_analyze_queries task asynchronously. %s" % e)
        raise e