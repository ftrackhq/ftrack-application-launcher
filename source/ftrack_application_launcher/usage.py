# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import logging
import os

import ftrack_api

from ftrack_application_launcher import asynchronous

logger = logging.getLogger('ftrack_application_launcher:usage')
_log_usage_session = None


def get_session():
    '''Return new ftrack_api session configure without plugins or events.'''
    # Create API session using credentials as stored by the application
    # when logging in.
    # TODO: Once API is thread-safe, consider switching to a shared session.
    return ftrack_api.Session(
        server_url=os.environ['FTRACK_SERVER'],
        api_key=os.environ['FTRACK_API_KEY'],
        api_user=os.environ['FTRACK_API_USER'],
        auto_connect_event_hub=False,
        plugin_paths=[]
    )


def _send_event(event_name, metadata=None):
    '''Send usage event with *event_name* and *metadata*.'''
    global _log_usage_session

    if _log_usage_session is None:
        _log_usage_session = get_session()

    try:
        _log_usage_session.call([{
            'action': '_track_usage',
            'data': {
                'type': 'event',
                'name': event_name,
                'metadata': metadata
            }
        }])
    except Exception:
        logger.exception('Failed to send event.')


@asynchronous.asynchronous
def _send_async_event(event_name, metadata=None):
    '''Call __send_event in a new thread.'''
    _send_event(event_name, metadata)


def send_event(event_name, metadata=None, asynchronous=True):
    '''Send usage event with *event_name* and *metadata*.

    If asynchronous is True, the event will be sent in a new thread.
    '''

    if asynchronous:
        _send_async_event(event_name, metadata)
    else:
        _send_event(event_name, metadata)
