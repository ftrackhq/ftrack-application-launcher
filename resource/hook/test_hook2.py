import ftrack_api
import logging

logger= logging.getLogger('test_hook2')


def on_discover_another(event):
    '''Handle application launch and add environment to *event*.'''
    logger.info('Discovering testing hook2')
    event['data']['integration']['name'] = 'another-connect-integration'
    event['data']['integration']['version'] = '10.0'
    return event


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    logger.info('discovering :{}'.format('app launcher testing hook2'))

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch',
        on_discover_another
    )
