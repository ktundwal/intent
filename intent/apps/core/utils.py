"""
utils
"""

import sys
import traceback
import logging

logger = logging.getLogger("intent")

def log_exception(message=''):
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

class UserMessage():
    def __init__(self, title="", text=[], url=None):
        self.title = title
        self.text = text if hasattr(text, '__iter__') else [text]
        self.url = url