from celery.task import task
from celery.task import periodic_task
from django.core.cache import cache
from time import sleep

from celery.decorators import periodic_task

from django.utils import timezone
from django.utils.timezone import utc, datetime, timedelta

from .utils import run_and_analyze_query, create_unknown_rule, intent_counts
from intent.apps.query.models import Rule, Author, Query, Document, DailyStat

from django.core.mail import send_mail
from intent.settings.common import *

import sys
import traceback

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

def update_stats(query, logger):
    counts = intent_counts(query)

    try:
        daily_stat = DailyStat.objects.filter(stat_of=query)[0]
        if not daily_stat:
            raise Exception
        daily_stat.document_count       = counts['docs_today_count']
        daily_stat.stat_for             = datetime.utcnow().replace(tzinfo=utc)
        daily_stat.buy_count            = counts['buy_today_count']
        daily_stat.recommendation_count = counts['recommendation_today_count']
        daily_stat.question_count       = counts['question_today_count']
        daily_stat.commitment_count     = counts['commitment_today_count']
        daily_stat.like_count           = counts['like_today_count']
        daily_stat.dislike_count        = counts['dislike_today_count']
        daily_stat.try_count            = counts['try_today_count']
        daily_stat.save()
    except Exception, ex:
        daily_stat = DailyStat.objects.create(
            stat_of              = query,
            stat_for             = datetime.utcnow().replace(tzinfo=utc),
            document_count       = counts['docs_today_count'],
            buy_count            = counts['buy_today_count'],
            recommendation_count = counts['recommendation_today_count'],
            question_count       = counts['question_today_count'],
            commitment_count     = counts['commitment_today_count'],
            like_count           = counts['like_today_count'],
            dislike_count        = counts['dislike_today_count'],
            try_count            = counts['try_today_count'],
        )
    logger.info('QUERY: %s, documents_created_today = %d. documents_count = %d'
        % (query.query, counts['docs_today_count'], counts['docs_all_count']))

    query.status = Query.WAITING_TO_RUN_STATUS
    query.last_run = datetime.utcnow().replace(tzinfo=utc)
    query.count = counts['docs_all_count']
    query.num_times_run += 1
    query.save()

    return daily_stat


def send_status_email(subject, message):
    send_mail(subject, message, DEFAULT_FROM_EMAIL, ['aloke@cruxly.com', 'kapil@cruxly.com'])

@periodic_task(run_every=timedelta(minutes=5))
def run_and_analyze_queries():
    response = None
    try:
        task_logger = run_and_analyze_queries.get_logger()

        queries = [query for query in Query.objects.filter(status=Query.WAITING_TO_RUN_STATUS)]
        task_logger.info("    Queries to run = %d" % len(queries))
        for query in queries:
            try:
                task_logger.info("    Running query %s for user %s" % (query.query, query.created_by))
                query.status = Query.RUNNING_STATUS
                query.save()
                tweets = run_and_analyze_query(query.query, query.count)

                # For each analyzed tweet, add a document
                for tweet in tweets:
                    try:
                        document = Document.objects.get(source_id=tweet['tweet_id'])
                    except Document.DoesNotExist:
                        document = None

                    if not document:
                        author = Author.objects.create(twitter_handle=tweet['author'], name='')
                        author.save()

                        document = Document.objects.create(
                            result_of=query,
                            source=Document.TWITTER_SOURCE,
                            author=author,
                            source_id=tweet['tweet_id'],
                            date=tweet['date'],
                            text=tweet['content'],
                            analyzed=True,

                            # for now we are not saving any rules. Just unknowns
                            buy_rule=create_unknown_rule(tweet['intents'], 'buy', Rule.BUY_GRAMMAR),
                            recommendation_rule=create_unknown_rule(tweet['intents'], 'recommendation',
                                Rule.RECOMMENDATION_GRAMMAR),
                            question_rule=create_unknown_rule(tweet['intents'], 'question', Rule.QUESTION_GRAMMAR),
                            commitment_rule=create_unknown_rule(tweet['intents'], 'commitment', Rule.COMMITMENT_GRAMMAR)
                            ,
                            like_rule=create_unknown_rule(tweet['intents'], 'like', Rule.LIKE_GRAMMAR),
                            dislike_rule=create_unknown_rule(tweet['intents'], 'dislike', Rule.DISLIKE_GRAMMAR),
                            try_rule=create_unknown_rule(tweet['intents'], 'tries', Rule.TRY_GRAMMAR),
                        )
                        document.save()
                    else:
                        # We have already analyzed this tweeet. may be we ran soon. SKIP
                        task_logger.info(
                            "    already analyzed tweeet. may be we ran soon. SKIPPING (%s)" % tweet['content'])

                daily_stat = update_stats(query, task_logger)

                try:
                    send_status_email('cruxly prod - background process success',
                        'Aloke, Kapil - successfully processed %s for user %s\n\n' % (query.query, query.created_by, daily_stat))
                except:
                    log_exception(task_logger, "Exception sending status via email. %s" % e)

            except Exception, e:
                response = '%s' % e
                log_exception(task_logger,
                    "Exception while processing query %s for user %s" % (query.query, query.created_by))
                query.last_run = datetime.utcnow().replace(tzinfo=utc)
                query.num_times_run += 1
                query.query_exception = e.message
                query.save()

                try:
                    send_status_email('cruxly prod - background process failure',
                        'Aloke, Kapil - exception processing %s for user %s\n\n %s' % (query.query, query.created_by, e))
                except:
                    log_exception(task_logger, "Exception sending status via email. %s" % e)
            finally:
                query.status = Query.WAITING_TO_RUN_STATUS
                query.save()
            task_logger.info("    Processed query %s for user %s" % (query.query, query.created_by))
    except Exception, e:
        response = '%s' % e
        log_exception(task_logger, "Exception while executing run_and_analyze_queries task asynchronously. %s" % e)

        try:
            send_status_email('cruxly prod - background process failure',
                'Aloke, Kapil - exception processing queries. %s' % e)
        except:
            log_exception(task_logger, "Exception sending status via email. %s" % e)

        raise e

    return response