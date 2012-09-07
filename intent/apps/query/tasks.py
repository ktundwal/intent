from celery.task import task
from celery.task import periodic_task
from django.core.cache import cache
from time import sleep

from celery.decorators import periodic_task

from django.utils import timezone
from django.utils.timezone import utc, datetime, timedelta

from .utils import *
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

def send_status_email(subject, message):
    message += '\n\n-Cruxly background query processor'
    send_mail(subject, message, DEFAULT_FROM_EMAIL, ['kapil@cruxly.com'])

@periodic_task(run_every=timedelta(minutes=5))
def run_and_analyze_queries():
    response = None
    email_message = ''
    try:
        task_logger = run_and_analyze_queries.get_logger()

        queries = [query for query in Query.objects.filter(status=Query.WAITING_TO_RUN_STATUS)]
        task_logger.info("    Queries to run = %d" % len(queries))
        for query in queries:
            try:
                task_logger.info("    Running query %s for user %s" % (query.query, query.created_by))
                query.status = Query.RUNNING_STATUS
                query.save()
                tweets = run_and_analyze_query(query.query, 500)

                dislike_count           = [tweet for tweet in tweets if 'dislike'           in tweet['intents']]
                question_count          = [tweet for tweet in tweets if 'question'          in tweet['intents']]
                recommendation_count    = [tweet for tweet in tweets if 'recommendation'    in tweet['intents']]
                buy_count               = [tweet for tweet in tweets if 'buy'               in tweet['intents']]
                commitment_count        = [tweet for tweet in tweets if 'commitment'        in tweet['intents']]
                try_count               = [tweet for tweet in tweets if 'try'               in tweet['intents']]
                like_count              = [tweet for tweet in tweets if 'like'              in tweet['intents']]

                query.question_count        += len(question_count)
                query.recommendation_count  += len(recommendation_count)
                query.buy_count             += len(buy_count)
                query.commitment_count      += len(commitment_count)
                query.try_count             += len(try_count)
                query.like_count            += len(like_count)
                query.dislike_count         += len(dislike_count)

                query.last_run = datetime.utcnow().replace(tzinfo=utc)
                query.num_times_run += 1
                query.count += len(tweets)
                query.save()

                daily_stat = get_or_create_todays_daily_stat(query)

                daily_stat.document_count        += len(tweets)
                daily_stat.question_count        += len(question_count)
                daily_stat.recommendation_count  += len(recommendation_count)
                daily_stat.buy_count             += len(buy_count)
                daily_stat.commitment_count      += len(commitment_count)
                daily_stat.try_count             += len(try_count)
                daily_stat.like_count            += len(like_count)
                daily_stat.dislike_count         += len(dislike_count)

                daily_stat.save()

                # For each analyzed tweet, add a document
                for tweet in tweets:
                    try:
                        document = Document.objects.get(source_id=tweet['tweet_id'])
                    except Document.DoesNotExist:
                        document = None

                    if not document:

                    # for now we are not saving any rules. Just unknowns
                        buy_rule=create_unknown_rule(tweet['intents'], 'buy', Rule.BUY_GRAMMAR)
                        recommendation_rule=create_unknown_rule(tweet['intents'], 'recommendation',
                            Rule.RECOMMENDATION_GRAMMAR)
                        question_rule=create_unknown_rule(tweet['intents'], 'question', Rule.QUESTION_GRAMMAR)
                        commitment_rule=create_unknown_rule(tweet['intents'], 'commitment', Rule.COMMITMENT_GRAMMAR)
                        like_rule=create_unknown_rule(tweet['intents'], 'like', Rule.LIKE_GRAMMAR)
                        dislike_rule=create_unknown_rule(tweet['intents'], 'dislike', Rule.DISLIKE_GRAMMAR)
                        try_rule=create_unknown_rule(tweet['intents'], 'tries', Rule.TRY_GRAMMAR)

                        if buy_rule or recommendation_rule or question_rule or commitment_rule \
                           or like_rule or dislike_rule or try_rule:

                            try:
                                author = Author.objects.get(twitter_handle=tweet['author'])
                            #except author.DoesNotExist:
                            except:
                                author = Author.objects.create(twitter_handle=tweet['author'], name='')

                            document = Document.objects.create(
                                result_of=query,
                                source=Document.TWITTER_SOURCE,
                                author=author,
                                source_id=tweet['tweet_id'],
                                date=tweet['date'],
                                text=tweet['content'],
                                analyzed=True,
                                # for now we are not saving any rules. Just unknowns
                                buy_rule=buy_rule,
                                recommendation_rule=recommendation_rule,
                                question_rule=question_rule,
                                commitment_rule=commitment_rule,
                                like_rule=like_rule,
                                dislike_rule=dislike_rule,
                                try_rule=try_rule,

                            )
                            document.save()
                    else:
                        # We have already analyzed this tweeet. may be we ran soon. SKIP
                        task_logger.info(
                            "    already analyzed tweeet. may be we ran soon. SKIPPING (%s)" % tweet['content'])

                task_logger.info("    Fetched %d tweets. Daily stat = %s" % (len(tweets), daily_stat.display()))
                email_message += '\n\n%s' % daily_stat.display()

            except Exception, e:
                response = '%s' % e
                log_exception(task_logger,
                    "Exception while processing query %s for user %s" % (query.query, query.created_by))
                query.query_exception = e.message
                query.save()

                try:
                    send_status_email('cruxly prod - background process failure',
                        'exception processing %s for user %s\n\n %s' % (query.query, query.created_by, e))
                except Exception, email_ex:
                    log_exception(task_logger, "Exception sending status via email. %s" % email_ex)
            finally:
                query.status = Query.WAITING_TO_RUN_STATUS
                query.save()
            task_logger.info("    Processed query %s for user %s" % (query.query, query.created_by))

        try:
            send_status_email('cruxly prod - background process success',
                'successfully processed %d queries.\n\n%s' % (len(queries), email_message))
        except Exception, email_ex:
            log_exception(task_logger, "Exception sending status via email \n%s" % email_ex)

    except Exception, e:
        response = '%s' % e
        log_exception(task_logger, "Exception while executing run_and_analyze_queries task asynchronously. %s" % e)

        try:
            send_status_email('cruxly prod - background process failure',
                'exception processing queries. %s' % e)
        except Exception, email_ex:
            log_exception(task_logger, "Exception sending status via email \n%s" % email_ex)

        raise e

    return response