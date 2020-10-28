import ftrack_api
import logging

logger= logging.getLogger('test_hook')


def on_discover_something(event):
    '''Handle application launch and add environment to *event*.'''
    logger.info('Discovering testing hook')
    event['data']['integration']['name'] = 'ftrack-connect-maya'
    event['data']['integration']['version'] = '1.0'
    return event


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    logger.info('discovering :{}'.format('ftrack.pipeline.discover'))
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch',
        on_discover_something, priority=20
    )
