# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import functools
import getpass
import sys
import pprint
import logging
import re
import os

import ftrack_api


def on_discover_maya_integration(session, event):

    cwd = os.path.dirname(__file__)
    sources = os.path.abspath(os.path.join(cwd, '..', 'dependencies'))
    ftrack_connect_maya_resource_path = os.path.abspath(os.path.join(cwd, '..',  'resource'))
    sys.path.append(sources)

    # from ftrack_connect_maya import __version__ as integration_version

    entity = event['data']['context']['selection'][0]
    task = session.get('Context', entity['entityId'])

    data = {
        'integration': {
            "name": 'ftrack-connect-maya'
            }
    }
    return data



def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return


    handle_event = functools.partial(
        on_discover_maya_integration,
        session
    )
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch'
        ' and data.application.identifier=maya*',
        handle_event
    )

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover'
        ' and data.application.identifier=maya*',
        handle_event
    )
