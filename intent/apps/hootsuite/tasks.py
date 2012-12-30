from datetime import date
from celery.task import periodic_task
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User

from django.utils.timezone import utc, datetime, timedelta

from intent.apps.query.utils import *
from .models import Stream, Document, Author, DailyStat, Rule

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

    streams = Stream.objects.all()
    for stream in streams:
        for user in users:
            streams = streams.exclude(created_by=user)

    for stream in streams:
        logger.info('Going to delete data older than 2 weeks for user %s, stream %s' % (stream.created_by, stream))
        two_weeks_ago = date.today() + relativedelta(weeks = -1)
        docs_older_than_two_weeks = Document.objects.filter(result_of=stream).filter(date__lte=two_weeks_ago)
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

def get_or_create_todays_daily_stat(stream):
    try:
        daily_stat = DailyStat.objects.filter(stat_of=stream, stat_for=datetime.utcnow().date())[0]
    except: # daily_stat.DoesNotExist:
        daily_stat = None

    if not daily_stat:
        daily_stat = DailyStat.objects.create(
            stat_of              = stream,
            stat_for             = datetime.utcnow().replace(tzinfo=utc))

    return daily_stat

@periodic_task(run_every=timedelta(minutes=5))
def run_and_analyze_queries():
    response = None
    email_message = ''
    try:
        task_logger = run_and_analyze_queries.get_logger()

        streams = [stream for stream in Stream.objects.filter(status=Stream.WAITING_TO_RUN_STATUS)]
        task_logger.info("    Queries to run = %d" % len(streams))
        for stream in streams:
            try:
                task_logger.info("    Running stream %s for user %s" % (stream.keywords, stream.created_by))
                stream.status = Stream.RUNNING_STATUS
                stream.save()

                tweets = run_and_analyze_query(Kip(keyterms=stream.keywords), 100, task_logger)

                #                tweets_w_dislike           = [tweet for tweet in tweets if {u'intent': u'dislike'}          in tweet['intents']]
                #                tweets_w_question          = [tweet for tweet in tweets if {u'intent': u'question'}         in tweet['intents']]
                #                tweets_w_recommendation    = [tweet for tweet in tweets if {u'intent': u'recommendation'}   in tweet['intents']]
                #                tweets_w_buy               = [tweet for tweet in tweets if {u'intent': u'buy'}              in tweet['intents']]
                #                tweets_w_commitment        = [tweet for tweet in tweets if {u'intent': u'commitment'}       in tweet['intents']]
                #                tweets_w_try               = [tweet for tweet in tweets if {u'intent': u'try'}              in tweet['intents']]
                #                tweets_w_like              = [tweet for tweet in tweets if {u'intent': u'like'}             in tweet['intents']]

                #                stream.question_count        += len(tweets_w_question)
                #                stream.recommendation_count  += len(tweets_w_recommendation)
                #                stream.buy_count             += len(tweets_w_buy)
                #                stream.commitment_count      += len(tweets_w_commitment)
                #                stream.try_count             += len(tweets_w_try)
                #                stream.like_count            += len(tweets_w_like)
                #                stream.dislike_count         += len(tweets_w_dislike)

                stream.last_run              = datetime.utcnow().replace(tzinfo=utc)
                stream.num_times_run         += 1
                #stream.count                 += len(tweets)
                stream.query_exception       = ""
                stream.save()

                daily_stat = get_or_create_todays_daily_stat(stream)

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

                        if buy_rule or recommendation_rule or question_rule or commitment_rule\
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
                                    result_of           = stream,
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
                                stream.count               += 1

                                if buy_rule:
                                    daily_stat.buy_count    += 1
                                    stream.buy_count         += 1
                                if recommendation_rule:
                                    daily_stat.recommendation_count    += 1
                                    stream.recommendation_count         += 1
                                if question_rule:
                                    daily_stat.question_count    += 1
                                    stream.question_count         += 1
                                if commitment_rule:
                                    daily_stat.commitment_count    += 1
                                    stream.commitment_count         += 1
                                if like_rule:
                                    daily_stat.like_count    += 1
                                    stream.like_count         += 1
                                if dislike_rule:
                                    daily_stat.dislike_count    += 1
                                    stream.dislike_count         += 1
                                if try_rule:
                                    daily_stat.try_count    += 1
                                    stream.try_count         += 1
                            except Exception, doc_e:
                                log_exception(task_logger, "Exception while processing document")
                    else:
                        # We have already analyzed this tweeet. may be we ran soon. SKIP
                        task_logger.info("    already analyzed tweeet. may be we ran soon. SKIPPING (%s)" % tweet['text'])

                    task_logger.info("    Fetched %d tweets. Daily stat = %s" % (len(tweets), daily_stat.display()))
                    #email_message += '\n\n%s' % daily_stat.display()

                stream.save()
                daily_stat.save()

            except Exception, e:
                response = '%s' % e
                log_exception(task_logger,
                    "Exception while processing stream %s for user %s" % (stream.keywords, stream.created_by))
                stream.query_exception = e.message
                stream.save()

                try:
                    send_status_email('cruxly prod - background process failure',
                        'exception processing %s for user %s\n\n %s' % (stream.keywords, stream.created_by, e))
                except Exception, email_ex:
                    #log_exception(task_logger, "Exception sending status via email. %s" % email_ex)
                    pass
            finally:
                try:
                    stream.status = Stream.WAITING_TO_RUN_STATUS
                    stream.save()
                except:
                    log_exception(task_logger, "Exception setting stream to in queue")
            task_logger.info("    Processed stream %s for user %s" % (stream.keywords, stream.created_by))

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