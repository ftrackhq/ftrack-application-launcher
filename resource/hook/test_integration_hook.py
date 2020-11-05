import ftrack_api
import logging

logger= logging.getLogger('test_hook')


def on_discover_something(event):
    '''Handle application launch and add environment to *event*.'''
    data = {
        'integration': {
            "name": 'ftrack-connect-maya',
            'version': 1.0
        },
        'env': {
            'MAYA_SCRIPT_PATH.prepend': 'SomeWhere'
        }
    }
    return data


def on_discover_another(event):
    '''Handle application launch and add environment to *event*.'''
    data = {
        'integration': {
            "name": 'another-connect-integration',
            'version': 1.0
        },
        'env': {
            'MAYA_SCRIPT_PATH.append': 'SomeWhereElse'
        }
    }
    return data


def on_discover_another_one(event):
    '''Handle application launch and add environment to *event*.'''
    data = {
        'integration': {
            "name": 'not-requested-at-all',
            'version': 1.0
        },
        'env': {'SOMETHING.set'}
    }
    return data


# def register(session):
#     '''Subscribe to application launch events on *registry*.'''
#     if not isinstance(session, ftrack_api.session.Session):
#         return

#     session.event_hub.subscribe(
#         'topic=ftrack.connect.application.launch',
#         on_discover_something
#     )

#     session.event_hub.subscribe(
#         'topic=ftrack.connect.application.launch',
#         on_discover_another
#     )

#     session.event_hub.subscribe(
#         'topic=ftrack.connect.application.launch',
#         on_discover_another_one
#     )