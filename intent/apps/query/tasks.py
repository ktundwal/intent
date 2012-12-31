from datetime import date
from celery.task import periodic_task
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User

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

def delete_data_older_then_two_weeks():

    emails_to_exclude = ['@gmail.com', '@yahoo.com', 'aol.com']
    users = User.objects.all()
    for exclude_email in emails_to_exclude:
        users = users.exclude(email__endswith=exclude_email)

    queries = Query.objects.all()
    for query in queries:
        for user in users:
            queries = queries.exclude(created_by=user)

    for query in queries:
        logger.info('Going to delete data older than 2 weeks for user %s, query %s' % (query.created_by, query))
        two_weeks_ago = date.today() + relativedelta(weeks = -1)
        docs_older_than_two_weeks = Document.objects.filter(result_of=query).filter(date__lte=two_weeks_ago)
        doc_count = docs_older_than_two_weeks.count()
        docs_older_than_two_weeks.delete()

        authors_with_deleted_tweets = Author.objects.filter(documents__isnull=True)
        author_count = authors_with_deleted_tweets.count()
        authors_with_deleted_tweets.delete()
        logger.info('Deleted %d tweets and %d authors that were older than 2 weeks' % (doc_count, author_count))

def create_unknown_rule(intents, intent_str, intent_id):
    rule = None

    if intent_str in intents:
        grammar_rule = "Unknown"
        grammar_version = "1.7"
        confidence = 1.0
        rule, created = Rule.objects.get_or_create(
            grammar=intent_id,
            grammar_version=grammar_version,
            rule=grammar_rule,
            confidence=confidence)

    return rule

def get_or_create_todays_daily_stat(query):
    try:
        daily_stat = DailyStat.objects.filter(stat_of=query, stat_for=datetime.utcnow().date())[0]
    except: # daily_stat.DoesNotExist:
        daily_stat = None

    if not daily_stat:
        daily_stat = DailyStat.objects.create(
            stat_of              = query,
            stat_for             = datetime.utcnow().replace(tzinfo=utc))

    return daily_stat

@periodic_task(run_every=timedelta(minutes=60))
def run_and_analyze_queries():
    response = None
    email_message = ''
    try:
        task_logger = run_and_analyze_queries.get_logger()

        queries = [query for query in Query.objects.filter(status=Query.WAITING_TO_RUN_STATUS) if query.created_by]
        task_logger.info("    Queries to run = %d" % len(queries))
        for query in queries:
            try:
                task_logger.info("    Running query %s for user %s" % (query.query, query.created_by))
                query.status = Query.RUNNING_STATUS
                query.save()

                tweets = run_and_analyze_query(Kip(keyterms=query.query, genericterms_comma_separated=query.industry_terms_comma_separated),
                    100, task_logger)

#                tweets_w_dislike           = [tweet for tweet in tweets if {u'intent': u'dislike'}          in tweet['intents']]
#                tweets_w_question          = [tweet for tweet in tweets if {u'intent': u'question'}         in tweet['intents']]
#                tweets_w_recommendation    = [tweet for tweet in tweets if {u'intent': u'recommendation'}   in tweet['intents']]
#                tweets_w_buy               = [tweet for tweet in tweets if {u'intent': u'buy'}              in tweet['intents']]
#                tweets_w_commitment        = [tweet for tweet in tweets if {u'intent': u'commitment'}       in tweet['intents']]
#                tweets_w_try               = [tweet for tweet in tweets if {u'intent': u'try'}              in tweet['intents']]
#                tweets_w_like              = [tweet for tweet in tweets if {u'intent': u'like'}             in tweet['intents']]

#                query.question_count        += len(tweets_w_question)
#                query.recommendation_count  += len(tweets_w_recommendation)
#                query.buy_count             += len(tweets_w_buy)
#                query.commitment_count      += len(tweets_w_commitment)
#                query.try_count             += len(tweets_w_try)
#                query.like_count            += len(tweets_w_like)
#                query.dislike_count         += len(tweets_w_dislike)

                query.last_run              = datetime.utcnow().replace(tzinfo=utc)
                query.num_times_run         += 1
                #query.count                 += len(tweets)
                query.query_exception       = ""
                query.save()

                daily_stat = get_or_create_todays_daily_stat(query)

#                daily_stat.document_count        += len(tweets)
#                daily_stat.question_count        += len(tweets_w_question)
#                daily_stat.recommendation_count  += len(tweets_w_recommendation)
#                daily_stat.buy_count             += len(tweets_w_buy)
#                daily_stat.commitment_count      += len(tweets_w_commitment)
#                daily_stat.try_count             += len(tweets_w_try)
#                daily_stat.like_count            += len(tweets_w_like)
#                daily_stat.dislike_count         += len(tweets_w_dislike)
#
#                daily_stat.save()

                # For each analyzed tweet, add a document
                for tweet in tweets:
                    try:
                        document = Document.objects.get(source_id=tweet['tweet_id'])
                    except Document.DoesNotExist:
                        document = None

                    if not document:

                        # for now we are not saving any rules. Just unknowns
                        buy_rule            = create_unknown_rule(tweet['intents'], {u'intent': u'buy'},           Rule.BUY_GRAMMAR)
                        recommendation_rule = create_unknown_rule(tweet['intents'], {u'intent': u'recommendation'},Rule.RECOMMENDATION_GRAMMAR)
                        question_rule       = create_unknown_rule(tweet['intents'], {u'intent': u'question'},      Rule.QUESTION_GRAMMAR)
                        commitment_rule     = create_unknown_rule(tweet['intents'], {u'intent': u'commitment'},    Rule.COMMITMENT_GRAMMAR)
                        like_rule           = create_unknown_rule(tweet['intents'], {u'intent': u'like'},          Rule.LIKE_GRAMMAR)
                        dislike_rule        = create_unknown_rule(tweet['intents'], {u'intent': u'dislike'},       Rule.DISLIKE_GRAMMAR)
                        try_rule            = create_unknown_rule(tweet['intents'], {u'intent': u'tries'},         Rule.TRY_GRAMMAR)

                        if buy_rule or recommendation_rule or question_rule or commitment_rule \
                           or like_rule or dislike_rule or try_rule:

                            try:
                                author = Author.objects.get(twitter_handle=tweet['author'])
                            #except author.DoesNotExist:
                            except:
                                author = Author.objects.create(twitter_handle=tweet['author'],
                                    name=tweet['author_user_name'],
                                    profile_image_url=tweet['image'])

#                            if tweet['geo']:
#                                lat = tweet['geo']['coordinates'][0]
#                                lng = tweet['geo']['coordinates'][1]
#                                place = None
#                            else:
#                                lat = None
#                                long = None
#                                place = None

                            try:
                                document = Document.objects.create(
                                    result_of           = query,
                                    source              = Document.TWITTER_SOURCE,
                                    author              = author,
                                    source_id           = tweet['tweet_id'],
                                    date                = datetime.strptime(tweet['date'], DATETIME_FORMAT),
                                    text                = tweet['text'],
                                    analyzed            = True,
                                    latitude            = tweet['latitude'],
                                    longitude           = tweet['longitude'],
                                    display_location    = None,
                                    # for now we are not saving any rules. Just unknowns
                                    buy_rule            = buy_rule,
                                    recommendation_rule = recommendation_rule,
                                    question_rule       = question_rule,
                                    commitment_rule     = commitment_rule,
                                    like_rule           = like_rule,
                                    dislike_rule        = dislike_rule,
                                    try_rule            = try_rule,

                                )
                                document.save()

                                daily_stat.document_count += 1
                                query.count               += 1

                                if buy_rule:
                                    daily_stat.buy_count    += 1
                                    query.buy_count         += 1
                                if recommendation_rule:
                                    daily_stat.recommendation_count    += 1
                                    query.recommendation_count         += 1
                                if question_rule:
                                    daily_stat.question_count    += 1
                                    query.question_count         += 1
                                if commitment_rule:
                                    daily_stat.commitment_count    += 1
                                    query.commitment_count         += 1
                                if like_rule:
                                    daily_stat.like_count    += 1
                                    query.like_count         += 1
                                if dislike_rule:
                                    daily_stat.dislike_count    += 1
                                    query.dislike_count         += 1
                                if try_rule:
                                    daily_stat.try_count    += 1
                                    query.try_count         += 1
                            except Exception, doc_e:
                                log_exception(task_logger, "Exception while processing document")
                    else:
                        # We have already analyzed this tweeet. may be we ran soon. SKIP
                        task_logger.info("    already analyzed tweeet. may be we ran soon. SKIPPING (%s)" % tweet['text'])

                    task_logger.info("    Fetched %d tweets. Daily stat = %s" % (len(tweets), daily_stat.display()))
                    #email_message += '\n\n%s' % daily_stat.display()

                query.save()
                daily_stat.save()

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
                    #log_exception(task_logger, "Exception sending status via email. %s" % email_ex)
                    pass
            finally:
                try:
                    query.status = Query.WAITING_TO_RUN_STATUS
                    query.save()
                except:
                    log_exception(task_logger, "Exception setting query to in queue")
            task_logger.info("    Processed query %s for user %s" % (query.query, query.created_by))

#        try:
#            send_status_email('cruxly prod - background process success',
#                'successfully processed %d queries.\n\n%s' % (len(queries), email_message))
#        except Exception, email_ex:
#            #log_exception(task_logger, "Exception sending status via email \n%s" % email_ex)
#            pass

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